import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models.models import StandardClause
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.models import Contract, Clause, RiskFlag, StandardClause
from utils.file_parser import FileParser
from services.clause_extractor import ClauseExtractor
from services.risk_analyzer import RiskAnalyzer

bp = Blueprint("contracts", __name__)

ALLOWED_EXTENSIONS = {"txt", "pdf", "docx"}


# ---------------------------------------------------
# Helper
# ---------------------------------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ===================================================
# CONTRACT ROUTES
# ===================================================

@bp.route("/contracts/upload", methods=["POST"])
@jwt_required()
def upload_contract():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Allowed: pdf, docx, txt"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    user_id = int(get_jwt_identity())

    contract = Contract(
        filename=filename,
        status="pending",
        user_id=user_id
    )

    db.session.add(contract)
    db.session.commit()

    return jsonify({
        "message": "File uploaded successfully",
        "contract_id": contract.id
    }), 201


@bp.route("/contracts", methods=["GET"])
@jwt_required()
def get_contracts():
    user_id = int(get_jwt_identity())

    contracts = Contract.query.filter_by(
        user_id=user_id
    ).order_by(Contract.upload_date.desc()).all()

    return jsonify([
        {
            "id": c.id,
            "filename": c.filename,
            "upload_date": c.upload_date.isoformat(),
            "status": c.status
        }
        for c in contracts
    ]), 200


@bp.route("/contracts/<int:contract_id>", methods=["DELETE"])
@jwt_required()
def delete_contract(contract_id):
    user_id = int(get_jwt_identity())
    contract = db.session.get(Contract, contract_id)

    if not contract or contract.user_id != user_id:
        return jsonify({"error": "Contract not found"}), 404

    try:
        filepath = os.path.join(
            current_app.config["UPLOAD_FOLDER"], contract.filename
        )
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass

    db.session.delete(contract)
    db.session.commit()

    return jsonify({"message": "Contract deleted successfully"}), 200


# ===================================================
# ANALYSIS ROUTES
# ===================================================

@bp.route("/analyze", methods=["POST"])
@jwt_required()
def analyze_contract():
    data = request.json
    contract_id = data.get("contract_id")

    if not contract_id:
        return jsonify({"error": "contract_id is required"}), 400

    user_id = int(get_jwt_identity())
    contract = db.session.get(Contract, contract_id)

    if not contract or contract.user_id != user_id:
        return jsonify({"error": "Contract not found"}), 404

    contract.status = "analyzing"
    db.session.commit()

    try:
        filepath = os.path.join(
            current_app.config["UPLOAD_FOLDER"], contract.filename
        )

        text = FileParser.parse_file(filepath)
        raw_clauses = ClauseExtractor.extract_clauses(text)

        analyzer = RiskAnalyzer.get_instance()
        analyzed_clauses = analyzer.analyze_batch(raw_clauses)

        Clause.query.filter_by(contract_id=contract.id).delete()

        for c_data in analyzed_clauses:
            clause = Clause(
                contract_id=contract.id,
                text=c_data["text"],
                clause_type=c_data["clause_type"],
                segment_index=c_data["segment_index"]
            )
            db.session.add(clause)
            db.session.flush()

            for r_data in c_data["risks"]:
                risk = RiskFlag(
                    clause_id=clause.id,
                    category=r_data["category"],
                    severity=r_data["severity"],
                    confidence=r_data["confidence"],
                    description=r_data["description"]
                )
                db.session.add(risk)

        contract.status = "completed"
        db.session.commit()

        return jsonify({"message": "Analysis complete"}), 200

    except Exception as e:
        db.session.rollback()
        contract.status = "failed"
        db.session.commit()
        return jsonify({"error": str(e)}), 500


@bp.route("/analysis/<int:contract_id>/summary", methods=["GET"])
@jwt_required()
def get_analysis_summary(contract_id):
    user_id = int(get_jwt_identity())
    contract = db.session.get(Contract, contract_id)

    if not contract or contract.user_id != user_id:
        return jsonify({"error": "Contract not found"}), 404

    clauses = Clause.query.filter_by(
        contract_id=contract.id
    ).order_by(Clause.segment_index).all()

    response = {
        "contract_id": contract.id,
        "filename": contract.filename,
        "status": contract.status,
        "clauses": []
    }

    for c in clauses:
        clause_data = {
            "id": c.id,
            "text": c.text,
            "clause_type": c.clause_type,
            "segment_index": c.segment_index,
            "risks": []
        }

        for r in c.risk_flags:
            clause_data["risks"].append({
                "id": r.id,
                "category": r.category,
                "severity": r.severity,
                "confidence": r.confidence,
                "description": r.description
            })

        response["clauses"].append(clause_data)

    return jsonify(response), 200


# ===================================================
# STANDARD CLAUSES ROUTES
# ===================================================

@bp.route("/standard-clauses", methods=["GET"])
@jwt_required()
def get_standard_clauses():
    clauses = StandardClause.query.order_by(
        StandardClause.created_at.desc()
    ).all()

    return jsonify([c.to_dict() for c in clauses]), 200


@bp.route("/standard-clauses", methods=["POST"])
@jwt_required()
def add_standard_clause():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    title = data.get("title")
    category = data.get("category")
    content = data.get("content")
    risk_level = data.get("risk_level")

    if not title or not category or not content:
        return jsonify({"error": "Title, category and content are required"}), 400

    clause = StandardClause(
        title=title,
        category=category,
        content=content,
        risk_level=risk_level
    )

    db.session.add(clause)
    db.session.commit()

    return jsonify({
        "message": "Standard clause added successfully",
        "clause": clause.to_dict()
    }), 201


@bp.route("/standard-clauses/<int:clause_id>", methods=["DELETE"])
@jwt_required()
def delete_standard_clause(clause_id):
    clause = db.session.get(StandardClause, clause_id)

    if not clause:
        return jsonify({"error": "Clause not found"}), 404

    db.session.delete(clause)
    db.session.commit()

    # ===================================================
# EMAIL REPORT ROUTE
# ===================================================

@bp.route("/contracts/<int:contract_id>/email", methods=["POST"])
@jwt_required()
def email_report(contract_id):
    user_id = int(get_jwt_identity())
    contract = db.session.get(Contract, contract_id)

    if not contract or contract.user_id != user_id:
        return jsonify({"error": "Contract not found"}), 404

    if contract.status != "completed":
        return jsonify({"error": "Analysis not complete yet"}), 400

    try:
        # Get user's email from DB
        from models.models import User
        user = db.session.get(User, user_id)
        if not user or not user.email:
            return jsonify({"error": "User email not found"}), 404

        # Fetch clauses + risk_flags
        clauses = Clause.query.filter_by(
            contract_id=contract.id
        ).order_by(Clause.segment_index).all()

        _send_analysis_email(user.email, contract.filename, clauses)

        return jsonify({"success": True, "message": "Email sent successfully"}), 200

    except Exception as e:
        current_app.logger.exception("Email send failed: %s", e)
        return jsonify({"error": str(e)}), 500


def _send_analysis_email(to_email, filename, clauses):
    sender   = os.environ.get("MAIL_USERNAME")
    password = os.environ.get("MAIL_PASSWORD")

    if not sender or not password:
        raise ValueError("MAIL_USERNAME or MAIL_PASSWORD not configured in environment")

    # Count risks by severity
    critical = sum(1 for c in clauses for r in c.risk_flags if r.severity == "critical")
    high     = sum(1 for c in clauses for r in c.risk_flags if r.severity == "high")
    medium   = sum(1 for c in clauses for r in c.risk_flags if r.severity == "medium")
    clean    = sum(1 for c in clauses if len(c.risk_flags) == 0)

    # Build clause details
    clause_lines = ""
    for i, c in enumerate(clauses, 1):
        if c.risk_flags:
            risks_str = "\n".join(
                f"      [{r.severity.upper()}] {r.category.replace('_', ' ').title()}: {r.description}"
                for r in c.risk_flags
            )
        else:
            risks_str = "      ✅ No risks detected"

        clause_lines += (
            f"\n{i}. {c.clause_type.replace('_', ' ').upper()}\n"
            f"   \"{c.text[:250]}{'...' if len(c.text) > 250 else ''}\"\n"
            f"   Risks:\n{risks_str}\n"
        )

    body = f"""
MY-LogiC — Contract Risk Analysis Report
==========================================
Document : {filename}
Generated: Auto-analyzed by MY-LogiC AI

━━━━━━━━━━━━━━━━━━━━━━━━
RISK SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━
  🔴 Critical : {critical}
  🟠 High     : {high}
  🟡 Medium   : {medium}
  🟢 Clean    : {clean}
  📄 Total    : {len(clauses)} clauses

━━━━━━━━━━━━━━━━━━━━━━━━
CLAUSE DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
{clause_lines}

━━━━━━━━━━━━━━━━━━━━━━━━
This report was automatically generated by MY-LogiC Contract AI.
Log in to view the full interactive analysis.
    """.strip()

    msg = MIMEMultipart()
    msg["From"]    = sender
    msg["To"]      = to_email
    msg["Subject"] = f"📄 MY-LogiC Risk Report: {filename}"
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, to_email, msg.as_string())

    return jsonify({"message": "Clause deleted successfully"}), 200 
