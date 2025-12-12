from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Concentrateur(Base):
    __tablename__ = "concentrateur"

    numero_serie = Column(String(50), primary_key=True, index=True)
    modele = Column(String(100), nullable=True)
    date_fabrication = Column(Date, nullable=True)
    operateur = Column(String(50), nullable=False, index=True)
    etat = Column(String(50), nullable=False, default="en_livraison", index=True)
    affectation = Column(String(100), nullable=True, index=True)
    hs = Column(Boolean, default=False)
    date_affectation = Column(DateTime, nullable=True)
    date_pose = Column(DateTime, nullable=True)
    date_dernier_etat = Column(DateTime, nullable=True)
    date_creation = Column(DateTime, default=datetime.utcnow)
    commentaire = Column(Text, nullable=True)
    photo = Column(String(500), nullable=True)
    
    # Foreign Keys
    numero_carton = Column(String(50), ForeignKey("carton.numero_carton"), nullable=True, index=True)
    poste_id = Column(Integer, ForeignKey("poste_electrique.id_poste"), nullable=True, index=True)
    commande_id = Column(Integer, ForeignKey("commande_bo.id_commande"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    carton = relationship("Carton", back_populates="concentrateurs")
    poste = relationship("PosteElectrique", back_populates="concentrateurs")
    commande = relationship("CommandeBo", back_populates="concentrateurs")
    actions = relationship("HistoriqueAction", back_populates="concentrateur")
