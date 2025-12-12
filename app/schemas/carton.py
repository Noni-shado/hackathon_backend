from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CartonBase(BaseModel):
    numero_carton: str
    operateur: str
    statut: str = "en_livraison"


class CartonResponse(CartonBase):
    date_reception: Optional[datetime] = None
    nombre_concentrateurs: int = 0

    class Config:
        from_attributes = True
