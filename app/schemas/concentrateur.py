from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class ConcentrateurBase(BaseModel):
    numero_serie: str
    modele: Optional[str] = None
    operateur: str
    etat: str = "en_livraison"
    affectation: Optional[str] = None


class ConcentrateurCreate(ConcentrateurBase):
    numero_carton: Optional[str] = None


class ConcentrateurUpdate(BaseModel):
    etat: Optional[str] = None
    affectation: Optional[str] = None
    poste_id: Optional[int] = None
    commentaire: Optional[str] = None
    hs: Optional[bool] = None


class ConcentrateurResponse(BaseModel):
    numero_serie: str
    modele: Optional[str] = None
    date_fabrication: Optional[date] = None
    operateur: str
    etat: str
    affectation: Optional[str] = None
    hs: bool = False
    date_affectation: Optional[datetime] = None
    date_pose: Optional[datetime] = None
    date_dernier_etat: Optional[datetime] = None
    commentaire: Optional[str] = None
    photo: Optional[str] = None
    numero_carton: Optional[str] = None
    poste_id: Optional[int] = None

    class Config:
        from_attributes = True


class HistoriqueActionResponse(BaseModel):
    id_action: int
    type_action: str
    date_action: datetime
    ancien_etat: Optional[str] = None
    nouvel_etat: Optional[str] = None
    ancienne_affectation: Optional[str] = None
    nouvelle_affectation: Optional[str] = None
    commentaire: Optional[str] = None
    scan_qr: bool = False
    photo: Optional[str] = None
    user_id: int

    class Config:
        from_attributes = True


class ConcentrateurListResponse(BaseModel):
    data: List[ConcentrateurResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class ConcentrateurDetailResponse(BaseModel):
    concentrateur: ConcentrateurResponse
    historique: List[HistoriqueActionResponse]


class ConcentrateurVerifyResponse(BaseModel):
    exists: bool
    concentrateur: Optional[ConcentrateurResponse] = None
