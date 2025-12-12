from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, is_admin
from app.models.user import Utilisateur
from app.models.concentrateur import Concentrateur
from app.models.action import HistoriqueAction

router = APIRouter()


class TestRequest(BaseModel):
    numero_serie: str
    resultat: str  # 'reparable' ou 'hs'
    commentaire: Optional[str] = None


@router.post("/test")
async def enregistrer_test(
    data: TestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Enregistrer le résultat d'un test de concentrateur.
    - Si réparable: retour au Magasin
    - Si HS: marqué comme HS
    - Réservé aux rôles admin et labo
    """
    # Vérifier le rôle
    if current_user.role not in ['admin', 'labo']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs et le personnel labo peuvent enregistrer des tests"
        )
    
    # Récupérer le concentrateur
    result = await db.execute(
        select(Concentrateur).where(Concentrateur.numero_serie == data.numero_serie)
    )
    concentrateur = result.scalar_one_or_none()
    
    if not concentrateur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concentrateur {data.numero_serie} non trouvé"
        )
    
    if concentrateur.affectation != 'Labo':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ce concentrateur n'est pas au Labo (affectation: {concentrateur.affectation})"
        )
    
    # Déterminer le nouvel état et affectation selon le résultat
    ancien_etat = concentrateur.etat
    ancienne_affectation = concentrateur.affectation
    
    if data.resultat == 'reparable':
        nouvel_etat = 'en_stock'
        nouvelle_affectation = 'Magasin'
        type_action = 'test_labo'
    elif data.resultat == 'hs':
        nouvel_etat = 'hs'
        nouvelle_affectation = 'Rebut'
        type_action = 'mise_au_rebut'
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Résultat invalide. Utilisez 'reparable' ou 'hs'"
        )
    
    # Mettre à jour le concentrateur
    concentrateur.etat = nouvel_etat
    concentrateur.affectation = nouvelle_affectation
    concentrateur.date_dernier_etat = datetime.utcnow()
    concentrateur.date_affectation = datetime.utcnow()
    concentrateur.hs = (data.resultat == 'hs')
    concentrateur.commentaire = data.commentaire
    
    # Créer l'action historique
    action = HistoriqueAction(
        type_action=type_action,
        ancien_etat=ancien_etat,
        nouvel_etat=nouvel_etat,
        ancienne_affectation=ancienne_affectation,
        nouvelle_affectation=nouvelle_affectation,
        commentaire=f"Test Labo: {data.resultat.upper()}. {data.commentaire or ''}".strip(),
        scan_qr=False,
        user_id=current_user.id_utilisateur,
        concentrateur_id=data.numero_serie,
    )
    db.add(action)
    
    await db.commit()
    
    return {
        "message": "Test enregistré",
        "numero_serie": data.numero_serie,
        "resultat": data.resultat,
        "nouvel_etat": nouvel_etat,
        "nouvelle_affectation": nouvelle_affectation
    }
