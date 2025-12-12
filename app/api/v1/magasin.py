from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user, is_admin
from app.models.user import Utilisateur
from app.models.concentrateur import Concentrateur
from app.models.action import HistoriqueAction

router = APIRouter()


class ReceptionRequest(BaseModel):
    numero_carton: str
    operateur: str
    quantite: int


class TransfertRequest(BaseModel):
    bo_destination: str
    concentrateurs: List[str]


@router.post("/reception")
async def reception_carton(
    data: ReceptionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Réception d'un carton fournisseur.
    Crée les concentrateurs avec état "en_stock" et affectation "Magasin".
    - Réservé aux rôles admin et magasin
    """
    # Vérifier le rôle
    if current_user.role not in ['admin', 'magasin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs et le personnel magasin peuvent effectuer des réceptions"
        )
    
    if data.quantite < 1 or data.quantite > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La quantité doit être entre 1 et 50"
        )
    
    created_concentrateurs = []
    
    for i in range(data.quantite):
        # Générer un numéro de série unique
        numero_serie = f"CPL-{data.operateur[:3].upper()}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        concentrateur = Concentrateur(
            numero_serie=numero_serie,
            operateur=data.operateur,
            etat='en_stock',
            affectation='Magasin',
            numero_carton=data.numero_carton,
            date_affectation=datetime.utcnow(),
            date_dernier_etat=datetime.utcnow(),
        )
        db.add(concentrateur)
        created_concentrateurs.append(numero_serie)
        
        # Créer l'action historique
        action = HistoriqueAction(
            type_action='reception_magasin',
            ancien_etat='en_livraison',
            nouvel_etat='en_stock',
            ancienne_affectation=None,
            nouvelle_affectation='Magasin',
            commentaire=f"Réception carton {data.numero_carton}",
            scan_qr=False,
            user_id=current_user.id_utilisateur,
            concentrateur_id=numero_serie,
            carton_id=data.numero_carton,
        )
        db.add(action)
    
    await db.commit()
    
    return {
        "message": "Réception validée",
        "created": len(created_concentrateurs),
        "concentrateurs": created_concentrateurs,
        "carton": data.numero_carton,
        "operateur": data.operateur
    }


@router.post("/transfert")
async def transfert_bo(
    data: TransfertRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Transfert de concentrateurs du Magasin vers une BO.
    - Réservé aux rôles admin et magasin
    """
    # Vérifier le rôle
    if current_user.role not in ['admin', 'magasin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs et le personnel magasin peuvent effectuer des transferts"
        )
    
    if not data.concentrateurs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun concentrateur sélectionné"
        )
    
    transferred = []
    errors = []
    
    for numero_serie in data.concentrateurs:
        # Récupérer le concentrateur
        result = await db.execute(
            select(Concentrateur).where(Concentrateur.numero_serie == numero_serie)
        )
        concentrateur = result.scalar_one_or_none()
        
        if not concentrateur:
            errors.append(f"{numero_serie}: introuvable")
            continue
        
        if concentrateur.affectation != 'Magasin':
            errors.append(f"{numero_serie}: pas au Magasin")
            continue
        
        # Mettre à jour le concentrateur
        ancien_affectation = concentrateur.affectation
        concentrateur.affectation = data.bo_destination
        concentrateur.date_affectation = datetime.utcnow()
        
        # Créer l'action historique
        action = HistoriqueAction(
            type_action='transfert_bo',
            ancien_etat=concentrateur.etat,
            nouvel_etat=concentrateur.etat,
            ancienne_affectation=ancien_affectation,
            nouvelle_affectation=data.bo_destination,
            commentaire=f"Transfert vers {data.bo_destination}",
            scan_qr=False,
            user_id=current_user.id_utilisateur,
            concentrateur_id=numero_serie,
        )
        db.add(action)
        transferred.append(numero_serie)
    
    await db.commit()
    
    return {
        "message": "Transfert effectué",
        "transferred": len(transferred),
        "concentrateurs": transferred,
        "destination": data.bo_destination,
        "errors": errors if errors else None
    }
