#!/usr/bin/env python3
"""
Script pour définir les mots de passe des utilisateurs.
Ajoute la colonne password_hash si elle n'existe pas et définit le mot de passe EDF2025!

Usage: python -m scripts.set_passwords
"""

import sys
import asyncio

sys.path.insert(0, '.')

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def main():
    print("=" * 60)
    print(" CONFIGURATION DES MOTS DE PASSE UTILISATEURS")
    print("=" * 60)
    
    # Créer l'engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    # Vérifier la connexion
    print("\n Connexion à Supabase...")
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print(" [OK] Connexion établie")
    except Exception as e:
        print(f" [ERREUR] Connexion échouée: {e}")
        await engine.dispose()
        sys.exit(1)
    
    # Vérifier si la colonne password_hash existe
    print("\n Vérification de la colonne password_hash...")
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'utilisateur' AND column_name = 'password_hash'
        """))
        column_exists = result.scalar_one_or_none()
    
    if not column_exists:
        print(" [INFO] Colonne password_hash non trouvée, ajout en cours...")
        async with engine.connect() as conn:
            await conn.execute(text("""
                ALTER TABLE utilisateur 
                ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)
            """))
            await conn.commit()
        print(" [OK] Colonne password_hash ajoutée")
    else:
        print(" [OK] Colonne password_hash existe déjà")
    
    # Générer le hash du mot de passe EDF2025!
    password = "EDF2025!"
    password_hash = pwd_context.hash(password)
    print(f"\n Mot de passe: {password}")
    print(f" Hash généré: {password_hash[:50]}...")
    
    # Mettre à jour TOUS les utilisateurs avec le nouveau mot de passe
    print("\n Mise à jour des utilisateurs...")
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            UPDATE utilisateur 
            SET password_hash = :hash 
            RETURNING email
        """), {"hash": password_hash})
        updated = result.fetchall()
        await conn.commit()
    
    if updated:
        print(f" [OK] {len(updated)} utilisateur(s) mis à jour:")
        for row in updated:
            print(f"     - {row[0]}")
    else:
        print(" [INFO] Aucun utilisateur à mettre à jour")
    
    # Vérifier l'utilisateur admin
    print("\n Vérification de l'utilisateur admin...")
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT email, nom, prenom, role, 
                   CASE WHEN password_hash IS NOT NULL AND password_hash != '' 
                        THEN 'OK' ELSE 'MISSING' END as pwd_status
            FROM utilisateur 
            WHERE email = 'admin@edf-corse.fr'
        """))
        admin = result.fetchone()
    
    if admin:
        print(f" Email: {admin[0]}")
        print(f" Nom: {admin[2]} {admin[1]}")
        print(f" Role: {admin[3]}")
        print(f" Password: {admin[4]}")
    else:
        print(" [WARN] Utilisateur admin@edf-corse.fr non trouvé")
    
    await engine.dispose()
    
    print("\n" + "=" * 60)
    print(" CONFIGURATION TERMINEE")
    print("=" * 60)
    print(f"\n Vous pouvez maintenant vous connecter avec:")
    print(f"   Email: admin@edf-corse.fr")
    print(f"   Mot de passe: {password}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
