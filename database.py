from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql+psycopg2://ritik:ritik@localhost:5432/ritik"

# -> sqlalchemy engine
engine = create_engine(DATABASE_URL)

# -> session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# -> base model
Base = declarative_base()


        