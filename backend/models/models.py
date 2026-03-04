from datetime import datetime
from . import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    contracts = db.relationship('Contract', backref='user', cascade='all, delete-orphan')

class Contract(db.Model):
    __tablename__ = 'contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pending') # pending, analyzing, completed, failed
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    clauses = db.relationship('Clause', backref='contract', cascade='all, delete-orphan')

class Clause(db.Model):
    __tablename__ = 'clauses'
    
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id', ondelete='CASCADE'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    clause_type = db.Column(db.String(100), nullable=True)
    segment_index = db.Column(db.Integer, nullable=False)
    
    # Relationships
    risk_flags = db.relationship('RiskFlag', backref='clause', cascade='all, delete-orphan')

class RiskFlag(db.Model):
    __tablename__ = 'risk_flags'
    
    id = db.Column(db.Integer, primary_key=True)
    clause_id = db.Column(db.Integer, db.ForeignKey('clauses.id', ondelete='CASCADE'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    severity = db.Column(db.String(20), nullable=False) # low, medium, high, critical
    confidence = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
