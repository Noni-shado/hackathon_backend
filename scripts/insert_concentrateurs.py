#!/usr/bin/env python3
"""
Script d'insertion des concentrateurs depuis le fichier SQL.
Lit le fichier 04_insert_concentrateurs.sql et exécute les INSERT par batch.

Usage: python -m scripts.insert_concentrateurs
"""

import sys
import asyncio
import re
from typing import List

sys.path.insert(0, '.')

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from app.core.config import settings


async def execute_sql_batch(engine, statements: List[str]) -> int:
    """Exécute un batch de statements SQL."""
    executed = 0
    async with engine.connect() as conn:
        for stmt in statements:
            try:
                await conn.execute(text(stmt))
                executed += 1
            except Exception as e:
                # Ignorer les erreurs de doublon ou de FK manquante
                error_str = str(e).lower()
                if 'duplicate' not in error_str and 'unique' not in error_str:
                    print(f"  [WARN] {str(e)[:80]}...")
        await conn.commit()
    return executed


async def main():
    print("=" * 60)
    print(" INSERTION DES CONCENTRATEURS DEPUIS SQL")
    print("=" * 60)
    
    # Chemin vers le fichier SQL
    sql_path = '../../sql/04_insert_concentrateurs.sql'
    
    print(f"\n Lecture du fichier SQL: {sql_path}")
    
    # Lire le fichier SQL
    try:
        with open(sql_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f" [ERREUR] Fichier SQL non trouvé: {sql_path}")
        sys.exit(1)
    
    # Extraire tous les INSERT statements
    # Pattern pour matcher les INSERT INTO concentrateur ... ;
    pattern = r"INSERT INTO concentrateur[^;]+;"
    statements = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
    
    print(f" {len(statements)} INSERT statements trouvés")
    
    if len(statements) == 0:
        print(" [ERREUR] Aucun INSERT trouvé dans le fichier")
        sys.exit(1)
    
    # Créer l'engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    # Vérifier la connexion
    print("\n Vérification de la connexion...")
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print(" [OK] Connexion établie")
    except Exception as e:
        print(f" [ERREUR] Connexion échouée: {e}")
        await engine.dispose()
        sys.exit(1)
    
    # Compter les concentrateurs avant
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM concentrateur"))
        count_before = result.scalar()
    print(f" Concentrateurs avant insertion: {count_before}")
    
    # Exécuter par batch de 50
    batch_size = 50
    total_executed = 0
    errors = 0
    
    print(f"\n Insertion par batch de {batch_size}...")
    
    for i in range(0, len(statements), batch_size):
        batch = statements[i:i + batch_size]
        executed = await execute_sql_batch(engine, batch)
        total_executed += executed
        errors += len(batch) - executed
        
        progress = min(i + batch_size, len(statements))
        pct = int(progress / len(statements) * 100)
        print(f"  [{pct:3d}%] {progress}/{len(statements)} traités")
    
    # Vérification finale
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM concentrateur"))
        count_after = result.scalar()
    
    await engine.dispose()
    
    print("\n" + "=" * 60)
    print(" INSERTION TERMINEE")
    print("=" * 60)
    print(f"\n Concentrateurs avant: {count_before}")
    print(f" Concentrateurs après: {count_after}")
    print(f" Nouveaux insérés: {count_after - count_before}")
    if errors > 0:
        print(f" Erreurs/doublons ignorés: {errors}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
