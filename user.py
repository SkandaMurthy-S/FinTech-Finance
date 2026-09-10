from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(50), nullable=False, default="Other")
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    transactions = db.relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    goals = db.relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    target = db.relationship("Target", back_populates="user", uselist=False, cascade="all, delete-orphan")

    @property
    def password(self):
        raise AttributeError("Password is not readable.")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_public_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "user_type": self.user_type,
            "bio": self.bio,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
