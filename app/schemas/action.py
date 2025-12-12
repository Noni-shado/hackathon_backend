from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HistoriqueActionBase(BaseModel):
    type_action: str
    ancien_etat: Optional[str] = None
    nouvel_etat: Optional[str] = None
    ancienne_affectation: Optional[str] = None
    nouvelle_affectation: Optional[str] = None
    commentaire: Optional[str] = None
    scan_qr: bool = False


class HistoriqueActionCreate(HistoriqueActionBase):
    concentrateur_id: Optional[str] = None
    carton_id: Optional[str] = None
    poste_id: Optional[int] = None


class HistoriqueActionResponse(HistoriqueActionBase):
    id_action: int
    date_action: datetime
    user_id: int
    concentrateur_id: Optional[str] = None
    carton_id: Optional[str] = None
    poste_id: Optional[int] = None
    photo: Optional[str] = None

    class Config:
        from_attributes = True
