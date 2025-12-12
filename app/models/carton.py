from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Carton(Base):
    __tablename__ = "carton"

    numero_carton = Column(String(50), primary_key=True, index=True)
    operateur = Column(String(50), nullable=False)
    date_reception = Column(DateTime, nullable=True)
    nombre_concentrateurs = Column(Integer, default=0)
    statut = Column(String(50), default="en_livraison")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    concentrateurs = relationship("Concentrateur", back_populates="carton")
    actions = relationship("HistoriqueAction", back_populates="carton")
