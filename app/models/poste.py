from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class PosteElectrique(Base):
    __tablename__ = "poste_electrique"

    id_poste = Column(Integer, primary_key=True, index=True)
    code_poste = Column(String(50), unique=True, nullable=False, index=True)
    nom_poste = Column(String(200), nullable=True)
    localisation = Column(String(200), nullable=True)
    bo_affectee = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    date_creation = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    concentrateurs = relationship("Concentrateur", back_populates="poste")
    actions = relationship("HistoriqueAction", back_populates="poste")
