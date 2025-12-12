from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class CommandeBo(Base):
    __tablename__ = "commande_bo"

    id_commande = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("utilisateur.id_utilisateur"), nullable=False)
    bo_demandeur = Column(String(100), nullable=False)
    quantite = Column(Integer, nullable=False)
    operateur_souhaite = Column(String(50), nullable=True)
    date_commande = Column(DateTime, default=datetime.utcnow)
    statut_commande = Column(String(50), default="en_attente")
    date_validation = Column(DateTime, nullable=True)
    date_livraison = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    utilisateur = relationship("Utilisateur", back_populates="commandes")
    concentrateurs = relationship("Concentrateur", back_populates="commande")
