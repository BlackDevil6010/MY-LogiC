import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.models import Contract, Clause, RiskFlag
from utils.file_parser import FileParser
from services.clause_extractor import ClauseExtractor
from services.risk_analyzer import RiskAnalyzer

bp = Blueprint('contracts', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        
    return jsonify({'error': 'Invalid file type. Allowed types: pdf, docx, txt'}), 400

@bp.route('/contracts', methods=['GET'])
@jwt_required()
def get_contracts():
    user_id = int(get_jwt_identity())
    contracts = Contract.query.filter_by(user_id=user_id).order_by(Contract.upload_date.desc()).all()
    result = []
    for c in contracts:
        result.append({
            'id': c.id,
            'filename': c.filename,
            'upload_date': c.upload_date.isoformat(),
            'status': c.status
        })
    return jsonify(result), 200

@bp.route('/contracts/<int:contract_id>', methods=['GET'])
@jwt_required()
def get_contract(contract_id):
    user_id = int(get_jwt_identity())
    contract = db.session.get(Contract, contract_id)
    if not contract or contract.user_id != user_id:
        return jsonify({'error': 'Contract not found'}), 404
        
    return jsonify({
        'id': contract.id,
        'filename': contract.filename,
        'status': contract.status,
        'upload_date': contract.upload_date.isoformat()
    }), 200

@bp.route('/contracts/<int:contract_id>', methods=['DELETE'])
@jwt_required()
def delete_contract(contract_id):
    try:
        user_id = int(get_jwt_identity())
        contract = db.session.get(Contract, contract_id)
        
        if not contract:
            return jsonify({'error': 'Contract not found in database'}), 404
            
        if contract.user_id != user_id:
            return jsonify({'error': 'Unauthorized: This contract does not belong to you'}), 403
            
        # Attempt to delete physical file
        try:
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], contract.filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            # We continue even if file deletion fails, to keep DB in sync
            print(f"Non-fatal error deleting file: {e}")
            
        db.session.delete(contract)
        db.session.commit()
        return jsonify({'message': 'Contract deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f"Internal server error: {str(e)}"}), 500

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
        
    contract.status = 'analyzing'
    db.session.commit()
    
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
        contract.status = 'failed'
        db.session.commit()
        return jsonify({'error': str(e)}), 500

@bp.route('/analysis/<int:contract_id>/summary', methods=['GET'])
@jwt_required()
def get_analysis_summary(contract_id):
    user_id = int(get_jwt_identity())
    contract = db.session.get(Contract, contract_id)
    if not contract or contract.user_id != user_id:
        return jsonify({'error': 'Contract not found'}), 404
        
    clauses = Clause.query.filter_by(contract_id=contract.id).order_by(Clause.segment_index).all()
    
    response = {
        'contract_id': contract.id,
        'filename': contract.filename,
        'status': contract.status,
        'clauses': []
    }
    
    for c in clauses:
        clause_data = {
            'id': c.id,
            'text': c.text,
            'clause_type': c.clause_type,
            'segment_index': c.segment_index,
            'risks': []
        }
        for r in c.risk_flags:
            clause_data['risks'].append({
                'id': r.id,
                'category': r.category,
                'severity': r.severity,
                'confidence': r.confidence,
                'description': r.description
            })
        response['clauses'].append(clause_data)
        
    return jsonify(response), 200
