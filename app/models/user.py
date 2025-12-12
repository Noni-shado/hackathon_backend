from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Utilisateur(Base):
    __tablename__ = "utilisateur"

    id_utilisateur = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="agent_terrain")
    date_inscription = Column(DateTime, default=datetime.utcnow)
    actif = Column(Boolean, default=True)
    telephone = Column(String(20), nullable=True)
    base_affectee = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    commandes = relationship("CommandeBo", back_populates="utilisateur")
    actions = relationship("HistoriqueAction", back_populates="utilisateur")
    notifications = relationship("Notification", back_populates="utilisateur")
    rapports = relationship("Rapport", back_populates="utilisateur")
