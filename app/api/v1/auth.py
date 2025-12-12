from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import verify_password, create_access_token, get_password_hash
from app.models.user import Utilisateur
from app.schemas.user import UserResponse

router = APIRouter()


@router.post("/login", response_model=dict)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Authentification utilisateur avec email et mot de passe.
    Retourne un token JWT.
    """
    result = await db.execute(
        select(Utilisateur).where(Utilisateur.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Pour le hackathon: si pas de password_hash, on accepte n'importe quel mot de passe
    # En production, décommenter la vérification ci-dessous
    if user.password_hash:
        if not verify_password(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou mot de passe incorrect",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    if not user.actif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte utilisateur désactivé"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id_utilisateur), "email": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id_utilisateur": user.id_utilisateur,
            "email": user.email,
            "nom": user.nom,
            "prenom": user.prenom,
            "role": user.role,
            "base_affectee": user.base_affectee,
            "telephone": user.telephone
        }
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Retourne les informations de l'utilisateur connecté.
    """
    return current_user


@router.post("/set-password")
async def set_password(
    password: str,
    current_user: Utilisateur = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Permet à l'utilisateur de définir/modifier son mot de passe.
    """
    current_user.password_hash = get_password_hash(password)
    await db.commit()
    return {"message": "Mot de passe mis à jour avec succès"}
