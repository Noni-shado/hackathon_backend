# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.declarative import declarative_base

# from app.core.config import settings

# engine = create_async_engine(
#     settings.DATABASE_URL,
#     echo=True,
#     future=True
# )

# AsyncSessionLocal = sessionmaker(
#     engine, class_=AsyncSession, expire_on_commit=False
# )

# Base = declarative_base()


# async def get_db():
#     async with AsyncSessionLocal() as session:
#         try:
#             yield session
#         finally:
#             await session.close()

# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.declarative import declarative_base

# from app.core.config import settings

# engine = create_async_engine(
#     settings.DATABASE_URL,
#     pool_pre_ping=True,   # évite connexions mortes
#     pool_recycle=300,     # recycle les connexions
#     echo=False            # IMPORTANT en prod / serverless
# )

# AsyncSessionLocal = sessionmaker(
#     engine,
#     class_=AsyncSession,
#     expire_on_commit=False
# )

# Base = declarative_base()


# async def get_db():
#     async with AsyncSessionLocal() as session:
#         yield session
