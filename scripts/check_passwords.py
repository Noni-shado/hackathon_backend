#!/usr/bin/env python3
"""
Script pour vérifier les mots de passe des utilisateurs.
"""

import sys
import asyncio

sys.path.insert(0, '.')

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from app.core.config import settings


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT email, 
                   CASE WHEN password_hash IS NOT NULL AND password_hash != '' 
                        THEN 'OUI' ELSE 'NON' END as has_password
            FROM utilisateur
            ORDER BY email
        """))
        
        print("\n=== UTILISATEURS ET MOTS DE PASSE ===\n")
        for row in result:
            print(f"  {row[0]}: {row[1]}")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
