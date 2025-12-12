from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Notification(Base):
    __tablename__ = "notification"

    id_notification = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("utilisateur.id_utilisateur"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    type_notification = Column(String(50), nullable=True)
    date_envoi = Column(DateTime, default=datetime.utcnow)
    lu = Column(Boolean, default=False, index=True)
    priorite = Column(String(20), default="normale")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    utilisateur = relationship("Utilisateur", back_populates="notifications")
