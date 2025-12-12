from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import Utilisateur

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Utilisateur:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    result = await db.execute(
        select(Utilisateur).where(Utilisateur.id_utilisateur == int(user_id))
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.actif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte utilisateur désactivé"
        )
    
    return user


async def get_current_active_admin(
    current_user: Utilisateur = Depends(get_current_user)
) -> Utilisateur:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Droits administrateur requis"
        )
    return current_user


def is_admin(user: Utilisateur) -> bool:
    """Vérifie si l'utilisateur est admin"""
    return user.role == "admin"


def get_user_bo_filter(user: Utilisateur) -> Optional[str]:
    """
    Retourne la BO à filtrer selon le rôle de l'utilisateur.
    - Admin: None (pas de filtre, accès à tout)
    - Autres: base_affectee de l'utilisateur
    """
    if is_admin(user):
        return None
    return user.base_affectee


def check_bo_access(user: Utilisateur, bo_name: str) -> bool:
    """
    Vérifie si l'utilisateur a accès à une BO spécifique.
    - Admin: accès à toutes les BOs
    - Autres: accès uniquement à leur base_affectee
    """
    if is_admin(user):
        return True
    return user.base_affectee == bo_name


def require_bo_access(user: Utilisateur, bo_name: str) -> None:
    """
    Lève une exception si l'utilisateur n'a pas accès à la BO.
    """
    if not check_bo_access(user, bo_name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Accès non autorisé à cette base opérationnelle"
        )
