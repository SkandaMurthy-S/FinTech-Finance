from datetime import datetime

from . import db


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    payment = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    note = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="transactions")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "amount": float(self.amount),
            "category": self.category,
            "payment": self.payment,
            "date": self.date.isoformat() if self.date else None,
            "note": self.note or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
