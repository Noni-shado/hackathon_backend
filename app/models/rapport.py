from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Rapport(Base):
    __tablename__ = "rapport"

    id_rapport = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("utilisateur.id_utilisateur"), nullable=False)
    type_rapport = Column(String(100), nullable=False)
    periode_debut = Column(DateTime, nullable=True)
    periode_fin = Column(DateTime, nullable=True)
    fichier = Column(String(500), nullable=True)
    date_generation = Column(DateTime, default=datetime.utcnow)
    format = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    utilisateur = relationship("Utilisateur", back_populates="rapports")
