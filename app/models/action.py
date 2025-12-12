from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class HistoriqueAction(Base):
    __tablename__ = "historique_action"

    id_action = Column(Integer, primary_key=True, index=True)
    type_action = Column(String(100), nullable=False, index=True)
    date_action = Column(DateTime, default=datetime.utcnow, index=True)
    ancien_etat = Column(String(50), nullable=True)
    nouvel_etat = Column(String(50), nullable=True)
    ancienne_affectation = Column(String(100), nullable=True)
    nouvelle_affectation = Column(String(100), nullable=True)
    commentaire = Column(Text, nullable=True)
    scan_qr = Column(Boolean, default=False)
    photo = Column(String(500), nullable=True)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("utilisateur.id_utilisateur"), nullable=False, index=True)
    concentrateur_id = Column(String(50), ForeignKey("concentrateur.numero_serie"), nullable=True, index=True)
    carton_id = Column(String(50), ForeignKey("carton.numero_carton"), nullable=True)
    poste_id = Column(Integer, ForeignKey("poste_electrique.id_poste"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    utilisateur = relationship("Utilisateur", back_populates="actions")
    concentrateur = relationship("Concentrateur", back_populates="actions")
    carton = relationship("Carton", back_populates="actions")
    poste = relationship("PosteElectrique", back_populates="actions")
