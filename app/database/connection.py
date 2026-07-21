from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Replace YOUR_PASSWORD with your PostgreSQL password
DATABASE_URL = (
    "postgresql+psycopg2://postgres:postgres123@localhost:5432/inspection_validation"
)

engine = create_engine(
    DATABASE_URL,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()