from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PosteElectriqueBase(BaseModel):
    code_poste: str
    nom_poste: Optional[str] = None
    localisation: Optional[str] = None
    bo_affectee: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PosteElectriqueResponse(PosteElectriqueBase):
    id_poste: int
    date_creation: Optional[datetime] = None

    class Config:
        from_attributes = True
