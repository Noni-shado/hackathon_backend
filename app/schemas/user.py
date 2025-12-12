from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    nom: str
    prenom: str
    role: str = "agent_terrain"
    base_affectee: Optional[str] = None
    telephone: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id_utilisateur: int
    email: str
    nom: str
    prenom: str
    role: str
    base_affectee: Optional[str] = None
    telephone: Optional[str] = None
    actif: bool = True
    date_inscription: Optional[datetime] = None

    class Config:
        from_attributes = True
