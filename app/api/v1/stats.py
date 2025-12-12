from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, and_
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import Utilisateur
from app.models.concentrateur import Concentrateur
from app.models.action import HistoriqueAction
from app.models.poste import PosteElectrique
from app.models.carton import Carton

router = APIRouter()


@router.get("/overview")
async def get_stats_overview(
    db: AsyncSession = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Statistiques globales pour le dashboard.
    """
    # Total concentrateurs
    result = await db.execute(select(func.count()).select_from(Concentrateur))
    total = result.scalar() or 0
    
    # Par état
    result = await db.execute(
        select(Concentrateur.etat, func.count())
        .group_by(Concentrateur.etat)
    )
    etats = {row[0]: row[1] for row in result}
    
    # En stock par affectation (Magasin vs BO)
    result = await db.execute(
        select(func.count())
        .where(and_(
            Concentrateur.etat == 'en_stock',
            Concentrateur.affectation == 'Magasin'
        ))
    )
    en_stock_magasin = result.scalar() or 0
    
    result = await db.execute(
        select(func.count())
        .where(and_(
            Concentrateur.etat == 'en_stock',
            Concentrateur.affectation.in_(['BO Nord', 'BO Sud', 'BO Centre'])
        ))
    )
    en_stock_bo = result.scalar() or 0
    
    # Actions aujourd'hui
    today = datetime.utcnow().date()
    result = await db.execute(
        select(func.count())
        .select_from(HistoriqueAction)
        .where(func.date(HistoriqueAction.date_action) == today)
    )
    actions_today = result.scalar() or 0
    
    # Totaux par table
    result = await db.execute(select(func.count()).select_from(PosteElectrique))
    total_postes = result.scalar() or 0
    
    result = await db.execute(select(func.count()).select_from(Carton))
    total_cartons = result.scalar() or 0
    
    result = await db.execute(select(func.count()).select_from(Utilisateur))
    total_utilisateurs = result.scalar() or 0
    
    return {
        "total_concentrateurs": total,
        "en_livraison": etats.get('en_livraison', 0),
        "en_stock": etats.get('en_stock', 0),
        "en_stock_magasin": en_stock_magasin,
        "en_stock_bo": en_stock_bo,
        "pose": etats.get('pose', 0),
        "retour_constructeur": etats.get('retour_constructeur', 0),
        "hs": etats.get('hs', 0),
        "actions_today": actions_today,
        "total_postes": total_postes,
        "total_cartons": total_cartons,
        "total_utilisateurs": total_utilisateurs
    }


@router.get("/stocks-par-base")
async def get_stocks_par_base(
    db: AsyncSession = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Répartition des stocks par base opérationnelle.
    """
    # Total global pour calculer les pourcentages
    result = await db.execute(select(func.count()).select_from(Concentrateur))
    total_global = result.scalar() or 1  # Éviter division par zéro
    
    # Stats par affectation
    result = await db.execute(
        select(
            Concentrateur.affectation,
            func.count().label('total'),
            func.sum(case((Concentrateur.etat == 'en_livraison', 1), else_=0)).label('en_livraison'),
            func.sum(case((Concentrateur.etat == 'en_stock', 1), else_=0)).label('en_stock'),
            func.sum(case((Concentrateur.etat == 'pose', 1), else_=0)).label('pose'),
            func.sum(case((Concentrateur.etat == 'retour_constructeur', 1), else_=0)).label('retour_constructeur'),
            func.sum(case((Concentrateur.etat == 'hs', 1), else_=0)).label('hs')
        )
        .where(Concentrateur.affectation.isnot(None))
        .group_by(Concentrateur.affectation)
        .order_by(func.count().desc())
    )
    
    stocks = []
    for row in result:
        total = row[1] or 0
        stocks.append({
            "base_operationnelle": row[0],
            "total": total,
            "en_livraison": row[2] or 0,
            "en_stock": row[3] or 0,
            "pose": row[4] or 0,
            "retour_constructeur": row[5] or 0,
            "hs": row[6] or 0,
            "percentage": round((total / total_global) * 100, 1) if total_global > 0 else 0
        })
    
    return stocks


@router.get("/actions-recentes")
async def get_actions_recentes(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Dernières actions effectuées.
    """
    result = await db.execute(
        select(HistoriqueAction)
        .order_by(HistoriqueAction.date_action.desc())
        .limit(limit)
    )
    actions = result.scalars().all()
    
    # Enrichir avec les infos utilisateur
    actions_enrichies = []
    for action in actions:
        # Récupérer l'utilisateur
        user_result = await db.execute(
            select(Utilisateur).where(Utilisateur.id_utilisateur == action.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        actions_enrichies.append({
            "id_action": action.id_action,
            "type_action": action.type_action,
            "date_action": action.date_action,
            "ancien_etat": action.ancien_etat,
            "nouvel_etat": action.nouvel_etat,
            "ancienne_affectation": action.ancienne_affectation,
            "nouvelle_affectation": action.nouvelle_affectation,
            "commentaire": action.commentaire,
            "concentrateur_id": action.concentrateur_id,
            "user": {
                "id": user.id_utilisateur if user else None,
                "nom": user.nom if user else "Inconnu",
                "prenom": user.prenom if user else "",
                "role": user.role if user else None
            } if user else None
        })
    
    return actions_enrichies


@router.get("/par-operateur")
async def get_stats_par_operateur(
    db: AsyncSession = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Répartition des concentrateurs par opérateur.
    """
    result = await db.execute(
        select(
            Concentrateur.operateur,
            func.count().label('total'),
            func.sum(case((Concentrateur.etat == 'en_stock', 1), else_=0)).label('en_stock'),
            func.sum(case((Concentrateur.etat == 'pose', 1), else_=0)).label('pose'),
            func.sum(case((Concentrateur.hs == True, 1), else_=0)).label('hs')
        )
        .group_by(Concentrateur.operateur)
        .order_by(func.count().desc())
    )
    
    operateurs = []
    for row in result:
        operateurs.append({
            "operateur": row[0],
            "total": row[1] or 0,
            "en_stock": row[2] or 0,
            "pose": row[3] or 0,
            "hs": row[4] or 0
        })
    
    return operateurs


@router.get("/postes-par-bo")
async def get_postes_par_bo(
    db: AsyncSession = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Répartition des postes électriques par BO.
    """
    result = await db.execute(
        select(PosteElectrique.bo_affectee, func.count())
        .group_by(PosteElectrique.bo_affectee)
        .order_by(func.count().desc())
    )
    
    return [{"bo": row[0], "count": row[1]} for row in result]
