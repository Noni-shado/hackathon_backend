from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_user, get_user_bo_filter, is_admin, require_bo_access
from app.models.user import Utilisateur
from app.models.concentrateur import Concentrateur
from app.models.action import HistoriqueAction
from app.schemas.concentrateur import (
    ConcentrateurResponse,
    ConcentrateurCreate,
    ConcentrateurUpdate,
    ConcentrateurListResponse,
    ConcentrateurDetailResponse,
    ConcentrateurVerifyResponse
)

router = APIRouter()


@router.get("", response_model=ConcentrateurListResponse)
async def get_concentrateurs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    etat: Optional[str] = None,
    affectation: Optional[str] = None,
    operateur: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Liste des concentrateurs avec pagination et filtres.
    - Admin: accès à tous les concentrateurs
    - Autres rôles: accès uniquement aux concentrateurs de leur BO
    """
    # Base query
    query = select(Concentrateur)
    count_query = select(func.count()).select_from(Concentrateur)
    
    # Filtres
    conditions = []
    
    # Filtre par BO selon le rôle de l'utilisateur
    bo_filter = get_user_bo_filter(current_user)
    if bo_filter:
        conditions.append(Concentrateur.affectation == bo_filter)
    
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                Concentrateur.numero_serie.ilike(search_pattern),
                Concentrateur.numero_carton.ilike(search_pattern),
                Concentrateur.operateur.ilike(search_pattern)
            )
        )
    
    if etat:
        conditions.append(Concentrateur.etat == etat)
    
    if affectation:
        conditions.append(Concentrateur.affectation == affectation)
    
    if operateur:
        conditions.append(Concentrateur.operateur == operateur)
    
    # Appliquer les conditions
    if conditions:
        for condition in conditions:
            query = query.where(condition)
            count_query = count_query.where(condition)
    
    # Compter le total
    result = await db.execute(count_query)
    total = result.scalar()
    
    # Pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit).order_by(Concentrateur.date_dernier_etat.desc())
    
    # Exécuter
    result = await db.execute(query)
    concentrateurs = result.scalars().all()
    
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    return {
        "data": concentrateurs,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


@router.get("/verify/{numero_serie}", response_model=ConcentrateurVerifyResponse)
async def verify_concentrateur(
    numero_serie: str,
    db: AsyncSession = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Vérifie si un concentrateur existe (pour scan QR rapide).
    """
    result = await db.execute(
        select(Concentrateur).where(Concentrateur.numero_serie == numero_serie)
    )
    concentrateur = result.scalar_one_or_none()
    
    return {
        "exists": concentrateur is not None,
        "concentrateur": concentrateur
    }


@router.get("/{numero_serie}", response_model=ConcentrateurDetailResponse)
async def get_concentrateur(
    numero_serie: str,
    db: AsyncSession = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Détail d'un concentrateur avec son historique d'actions.
    - Admin: accès à tous les concentrateurs
    - Autres rôles: accès uniquement aux concentrateurs de leur BO
    """
    # Récupérer le concentrateur
    result = await db.execute(
        select(Concentrateur).where(Concentrateur.numero_serie == numero_serie)
    )
    concentrateur = result.scalar_one_or_none()
    
    if not concentrateur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concentrateur {numero_serie} non trouvé"
        )
    
    # Vérifier l'accès selon le rôle
    if concentrateur.affectation:
        require_bo_access(current_user, concentrateur.affectation)
    
    # Récupérer l'historique des actions
    result = await db.execute(
        select(HistoriqueAction)
        .where(HistoriqueAction.concentrateur_id == numero_serie)
        .order_by(HistoriqueAction.date_action.desc())
    )
    historique = result.scalars().all()
    
    return {
        "concentrateur": concentrateur,
        "historique": historique
    }


@router.post("", response_model=ConcentrateurResponse, status_code=status.HTTP_201_CREATED)
async def create_concentrateur(
    data: ConcentrateurCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Créer un nouveau concentrateur.
    Réservé aux rôles admin et gestionnaire.
    """
    # Vérifier le rôle
    if current_user.role not in ['admin', 'gestionnaire']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs et gestionnaires peuvent créer des concentrateurs"
        )
    
    # Vérifier si le numéro de série existe déjà
    result = await db.execute(
        select(Concentrateur).where(Concentrateur.numero_serie == data.numero_serie)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le concentrateur {data.numero_serie} existe déjà"
        )
    
    # Déterminer l'état initial
    etat_initial = 'en_stock' if data.affectation == 'Magasin' else 'en_livraison'
    
    # Créer le concentrateur
    concentrateur = Concentrateur(
        numero_serie=data.numero_serie,
        modele=data.modele,
        operateur=data.operateur,
        etat=etat_initial,
        affectation=data.affectation,
        numero_carton=data.numero_carton,
        date_affectation=datetime.utcnow(),
        date_dernier_etat=datetime.utcnow(),
        hs=False
    )
    
    db.add(concentrateur)
    
    # Créer l'action de réception
    action = HistoriqueAction(
        type_action='reception_magasin',
        nouvel_etat=etat_initial,
        nouvelle_affectation=data.affectation,
        user_id=current_user.id_utilisateur,
        concentrateur_id=data.numero_serie
    )
    
    db.add(action)
    await db.commit()
    await db.refresh(concentrateur)
    
    return concentrateur


@router.put("/{numero_serie}", response_model=ConcentrateurResponse)
async def update_concentrateur(
    numero_serie: str,
    data: ConcentrateurUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Mettre à jour un concentrateur.
    """
    # Récupérer le concentrateur
    result = await db.execute(
        select(Concentrateur).where(Concentrateur.numero_serie == numero_serie)
    )
    concentrateur = result.scalar_one_or_none()
    
    if not concentrateur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concentrateur {numero_serie} non trouvé"
        )
    
    # Sauvegarder les anciennes valeurs pour l'historique
    ancien_etat = concentrateur.etat
    ancienne_affectation = concentrateur.affectation
    
    # Mettre à jour les champs
    update_data = data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(concentrateur, field, value)
    
    concentrateur.date_dernier_etat = datetime.utcnow()
    
    # Créer une action si l'état ou l'affectation a changé
    if data.etat or data.affectation:
        action = HistoriqueAction(
            type_action='modification',
            ancien_etat=ancien_etat,
            nouvel_etat=data.etat or ancien_etat,
            ancienne_affectation=ancienne_affectation,
            nouvelle_affectation=data.affectation or ancienne_affectation,
            commentaire=data.commentaire,
            user_id=current_user.id_utilisateur,
            concentrateur_id=numero_serie
        )
        db.add(action)
    
    await db.commit()
    await db.refresh(concentrateur)
    
    return concentrateur


@router.get("/stats/overview")
async def get_concentrateurs_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Statistiques des concentrateurs.
    - Admin: stats globales
    - Autres rôles: stats de leur BO uniquement
    """
    # Filtre par BO selon le rôle
    bo_filter = get_user_bo_filter(current_user)
    
    # Total
    count_query = select(func.count()).select_from(Concentrateur)
    if bo_filter:
        count_query = count_query.where(Concentrateur.affectation == bo_filter)
    result = await db.execute(count_query)
    total = result.scalar()
    
    # Par état
    etat_query = select(Concentrateur.etat, func.count()).group_by(Concentrateur.etat)
    if bo_filter:
        etat_query = etat_query.where(Concentrateur.affectation == bo_filter)
    result = await db.execute(etat_query)
    par_etat = {row[0]: row[1] for row in result}
    
    # Par opérateur
    operateur_query = select(Concentrateur.operateur, func.count()).group_by(Concentrateur.operateur)
    if bo_filter:
        operateur_query = operateur_query.where(Concentrateur.affectation == bo_filter)
    result = await db.execute(operateur_query)
    par_operateur = {row[0]: row[1] for row in result}
    
    # Par affectation (seulement pour admin)
    par_affectation = {}
    if is_admin(current_user):
        result = await db.execute(
            select(Concentrateur.affectation, func.count())
            .where(Concentrateur.affectation.isnot(None))
            .group_by(Concentrateur.affectation)
        )
        par_affectation = {row[0]: row[1] for row in result}
    else:
        par_affectation = {bo_filter: total} if bo_filter else {}
    
    return {
        "total": total,
        "par_etat": par_etat,
        "par_operateur": par_operateur,
        "par_affectation": par_affectation
    }
