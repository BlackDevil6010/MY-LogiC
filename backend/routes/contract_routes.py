import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.models import Contract, Clause, RiskFlag
from utils.file_parser import FileParser
from services.clause_extractor import ClauseExtractor
from services.risk_analyzer import RiskAnalyzer

bp = Blueprint('contracts', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# -----------------------------
# Upload Contract
# -----------------------------
@bp.route('/contracts/upload', methods=['POST'])
@jwt_required()
def upload_contract():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        user_id = int(get_jwt_identity())
        contract = Contract(filename=filename, status='pending', user_id=user_id)
        db.session.add(contract)
        db.session.commit()

        return jsonify({
            'message': 'File uploaded successfully',
            'contract_id': contract.id
        }), 201

    return jsonify({'error': 'Invalid file type'}), 400


# -----------------------------
# Analyze Contract
# -----------------------------
@bp.route('/analyze', methods=['POST'])
@jwt_required()
def analyze_contract():
    data = request.json
    contract_id = data.get('contract_id')

    if not contract_id:
        return jsonify({'error': 'contract_id is required'}), 400

    user_id = int(get_jwt_identity())
    contract = db.session.get(Contract, contract_id)

    if not contract or contract.user_id != user_id:
        return jsonify({'error': 'Contract not found'}), 404

    try:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], contract.filename)
        text = FileParser.parse_file(filepath)

        raw_clauses = ClauseExtractor.extract_clauses(text)
        analyzer = RiskAnalyzer.get_instance()
        analyzed_clauses = analyzer.analyze_batch(raw_clauses)

        Clause.query.filter_by(contract_id=contract.id).delete()

        for c_data in analyzed_clauses:
            clause = Clause(
                contract_id=contract.id,
                text=c_data['text'],
                clause_type=c_data['clause_type'],
                segment_index=c_data['segment_index']
            )
            db.session.add(clause)
            db.session.flush()

            for r_data in c_data['risks']:
                risk = RiskFlag(
                    clause_id=clause.id,
                    category=r_data['category'],
                    severity=r_data['severity'],
                    confidence=r_data['confidence'],
                    description=r_data['description']
                )
                db.session.add(risk)

        contract.status = 'completed'
        db.session.commit()

        return jsonify({'message': 'Analysis complete'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# -----------------------------
# Send Email Report
# -----------------------------
@bp.route('/analysis/<int:contract_id>/email', methods=['POST'])
@jwt_required()
def email_analysis_summary(contract_id):

    data = request.json
    recipient_email = data.get('email')

    if not recipient_email:
        return jsonify({'error': 'recipient email is required'}), 400

    user_id = int(get_jwt_identity())
    contract = db.session.get(Contract, contract_id)

    if not contract or contract.user_id != user_id:
        return jsonify({'error': 'Contract not found'}), 404

    clauses = Clause.query.filter_by(contract_id=contract.id).all()

    html_content = f"<h2>Contract Risk Analysis: {contract.filename}</h2>"
    html_content += f"<p>Status: {contract.status}</p>"

    for c in clauses:
        if c.risk_flags:
            html_content += "<hr>"
            html_content += f"<p><strong>Clause:</strong> {c.text}</p>"
            html_content += "<ul>"
            for r in c.risk_flags:
                html_content += f"<li><b>{r.severity.upper()}</b>: {r.description}</li>"
            html_content += "</ul>"

    try:
        sender = current_app.config['MAIL_DEFAULT_SENDER']
        username = current_app.config['MAIL_USERNAME']
        password = current_app.config['MAIL_PASSWORD']

        subject = f"Contract Analysis Report: {contract.filename}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient_email

        msg.attach(MIMEText(html_content, "html"))

        server = smtplib.SMTP(
            current_app.config['MAIL_SERVER'],
            current_app.config['MAIL_PORT']
        )

        server.starttls()
        server.login(username, password)
        server.sendmail(sender, recipient_email, msg.as_string())
        server.quit()

        return jsonify({'message': 'Email sent successfully'}), 200

    except Exception as e:
        print("EMAIL ERROR:", str(e))
        return jsonify({'error': str(e)}), 500
