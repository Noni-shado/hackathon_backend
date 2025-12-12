#!/usr/bin/env python3
"""
Script de vérification de la connexion à Supabase
et des données présentes dans la base de données.

Usage: python -m scripts.verify_database
"""

import sys
import asyncio
from typing import List, Tuple, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Ajouter le chemin parent pour les imports
sys.path.insert(0, '.')

from app.core.config import settings


def print_header(title: str) -> None:
    """Affiche un header formaté."""
    print(f"\n{'=' * 50}")
    print(f" {title}")
    print('=' * 50)


def print_table(headers: List[str], rows: List[Tuple[Any, ...]]) -> None:
    """Affiche un tableau formaté."""
    if not rows:
        print(" (aucune donnée)")
        return
        
    col_widths = [max(len(str(h)), max(len(str(r[i])) for r in rows) if rows else 0) 
                  for i, h in enumerate(headers)]
    
    # Header
    header_line = " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))
    separator = "-+-".join("-" * w for w in col_widths)
    
    print(f" {header_line}")
    print(f" {separator}")
    
    # Rows
    for row in rows:
        row_line = " | ".join(f"{str(r):<{col_widths[i]}}" for i, r in enumerate(row))
        print(f" {row_line}")


async def test_connection(engine) -> bool:
    """Teste la connexion à la base de données."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print(" [OK] Connexion réussie à Supabase")
        return True
    except Exception as e:
        print(f" [ERREUR] Connexion échouée: {e}")
        return False


async def get_tables(engine) -> List[str]:
    """Récupère la liste des tables."""
    query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(query))
            return [row[0] for row in result]
    except Exception:
        return []


async def count_table_rows(engine, table_name: str) -> int:
    """Compte le nombre de lignes dans une table."""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
    except Exception:
        return -1


async def get_concentrateurs_by_etat(engine) -> List[Tuple[str, int]]:
    """Récupère le nombre de concentrateurs par état."""
    query = """
        SELECT etat, COUNT(*) as count 
        FROM concentrateur 
        GROUP BY etat 
        ORDER BY count DESC
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(query))
            return [(row[0], row[1]) for row in result]
    except Exception:
        return []


async def get_concentrateurs_by_operateur(engine) -> List[Tuple[str, int]]:
    """Récupère le nombre de concentrateurs par opérateur."""
    query = """
        SELECT operateur, COUNT(*) as count 
        FROM concentrateur 
        GROUP BY operateur 
        ORDER BY count DESC
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(query))
            return [(row[0], row[1]) for row in result]
    except Exception:
        return []


async def get_postes_by_bo(engine) -> List[Tuple[str, int]]:
    """Récupère le nombre de postes par BO affectée."""
    query = """
        SELECT bo_affectee, COUNT(*) as count 
        FROM poste_electrique 
        GROUP BY bo_affectee 
        ORDER BY count DESC
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(query))
            return [(row[0], row[1]) for row in result]
    except Exception:
        return []


async def get_users_by_role(engine) -> List[Tuple[str, int]]:
    """Récupère le nombre d'utilisateurs par rôle."""
    query = """
        SELECT role, COUNT(*) as count 
        FROM utilisateur 
        GROUP BY role 
        ORDER BY count DESC
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(query))
            return [(row[0], row[1]) for row in result]
    except Exception:
        return []


async def get_sample_users(engine, limit: int = 3) -> List[Tuple[str, str, str]]:
    """Récupère quelques exemples d'utilisateurs."""
    query = f"""
        SELECT email, role, COALESCE(base_affectee, 'N/A') 
        FROM utilisateur 
        LIMIT {limit}
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(query))
            return [(row[0], row[1], row[2]) for row in result]
    except Exception:
        return []


async def get_sample_concentrateurs(engine, limit: int = 3) -> List[Tuple[str, str, str]]:
    """Récupère quelques exemples de concentrateurs."""
    query = f"""
        SELECT numero_serie, operateur, etat 
        FROM concentrateur 
        LIMIT {limit}
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(query))
            return [(row[0], row[1], row[2]) for row in result]
    except Exception:
        return []


async def main() -> None:
    """Fonction principale de vérification."""
    print_header("VERIFICATION BASE DE DONNEES SUPABASE")
    
    # Création de l'engine async
    print(f"\n Database URL: {settings.DATABASE_URL[:50]}...")
    
    try:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
    except Exception as e:
        print(f" [ERREUR] Impossible de créer l'engine: {e}")
        sys.exit(1)
    
    # Test connexion
    print("\n--- Test de connexion ---")
    if not await test_connection(engine):
        await engine.dispose()
        sys.exit(1)
    
    # Liste des tables
    print("\n--- Tables détectées ---")
    tables = await get_tables(engine)
    expected_tables = [
        'utilisateur', 'poste_electrique', 'carton', 'concentrateur',
        'commande_bo', 'historique_action', 'notification', 'rapport'
    ]
    
    for table in expected_tables:
        status = "[OK]" if table in tables else "[MANQUANTE]"
        print(f" {status} {table}")
    
    # Comptage par table
    print("\n--- Nombre d'enregistrements par table ---")
    table_counts = []
    for table in expected_tables:
        if table in tables:
            count = await count_table_rows(engine, table)
            table_counts.append((table, count))
    
    print_table(["Table", "Count"], table_counts)
    
    # Statistiques concentrateurs par état
    print("\n--- Concentrateurs par état ---")
    etats = await get_concentrateurs_by_etat(engine)
    for etat, count in etats:
        print(f" - {etat}: {count}")
    
    # Statistiques concentrateurs par opérateur
    print("\n--- Concentrateurs par opérateur ---")
    operateurs = await get_concentrateurs_by_operateur(engine)
    for operateur, count in operateurs:
        print(f" - {operateur}: {count}")
    
    # Statistiques postes par BO
    print("\n--- Postes par BO affectée ---")
    bos = await get_postes_by_bo(engine)
    for bo, count in bos:
        print(f" - {bo}: {count}")
    
    # Statistiques utilisateurs par rôle
    print("\n--- Utilisateurs par rôle ---")
    roles = await get_users_by_role(engine)
    for role, count in roles:
        print(f" - {role}: {count}")
    
    # Exemples d'utilisateurs
    print("\n--- Exemples d'utilisateurs ---")
    users = await get_sample_users(engine)
    for email, role, base in users:
        print(f" - {email} ({role}, {base})")
    
    # Exemples de concentrateurs
    print("\n--- Exemples de concentrateurs ---")
    concentrateurs = await get_sample_concentrateurs(engine)
    for numero, operateur, etat in concentrateurs:
        print(f" - {numero} ({operateur}, {etat})")
    
    # Fermer l'engine
    await engine.dispose()
    
    print_header("VERIFICATION TERMINEE")
    print("\n [OK] Base de données Supabase opérationnelle!\n")


if __name__ == "__main__":
    asyncio.run(main())
