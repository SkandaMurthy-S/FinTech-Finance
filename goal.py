from datetime import datetime

from . import db


class Goal(db.Model):
    __tablename__ = "goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    saved = db.Column(db.Float, default=0.0, nullable=False)
    target_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="goals")

    def to_dict(self):
        progress = 0.0
        if self.amount > 0:
            progress = min((self.saved / self.amount) * 100, 100)
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "amount": float(self.amount),
            "saved": float(self.saved),
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "progress": round(progress, 2),
            "remaining": max(float(self.amount - self.saved), 0.0),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
