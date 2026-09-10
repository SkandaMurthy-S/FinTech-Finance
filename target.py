from datetime import datetime

from . import db


class Target(db.Model):
    __tablename__ = "targets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    income_target = db.Column(db.Float, default=0.0, nullable=False)
    expense_target = db.Column(db.Float, default=0.0, nullable=False)
    savings_target = db.Column(db.Float, default=0.0, nullable=False)
    food_target = db.Column(db.Float, default=0.0, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="target")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "income_target": float(self.income_target),
            "expense_target": float(self.expense_target),
            "savings_target": float(self.savings_target),
            "food_target": float(self.food_target),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
