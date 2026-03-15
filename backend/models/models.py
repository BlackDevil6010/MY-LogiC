from datetime import datetime
from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    contracts = db.relationship(
        "Contract",
        backref="user",
        cascade="all, delete-orphan",
        lazy=True
    )


class Contract(db.Model):
    __tablename__ = "contracts"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="pending")

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    clauses = db.relationship(
        "Clause",
        backref="contract",
        cascade="all, delete-orphan",
        lazy=True
    )


class Clause(db.Model):
    __tablename__ = "clauses"

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(
        db.Integer,
        db.ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False
    )

    text = db.Column(db.Text, nullable=False)
    clause_type = db.Column(db.String(100))
    segment_index = db.Column(db.Integer, nullable=False)

    risk_flags = db.relationship(
        "RiskFlag",
        backref="clause",
        cascade="all, delete-orphan",
        lazy=True
    )


class RiskFlag(db.Model):
    __tablename__ = "risk_flags"

    id = db.Column(db.Integer, primary_key=True)
    clause_id = db.Column(
        db.Integer,
        db.ForeignKey("clauses.id", ondelete="CASCADE"),
        nullable=False
    )

    category = db.Column(db.String(100), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)


# ✅ NEW TABLE FOR STANDARD CLAUSES
class StandardClause(db.Model):
    __tablename__ = "standard_clauses"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    risk_level = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "content": self.content,
            "risk_level": self.risk_level,
            "created_at": self.created_at.isoformat()
        }
