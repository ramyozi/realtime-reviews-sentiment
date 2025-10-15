import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

# 📦 Load environment variables
# Priority order:
# 1. .env.local.local  → for development
# 2. .env.local.prod   → for production
# 3. .env.local        → fallback default

if os.path.exists(".env.local.local"):
    load_dotenv(".env.local.local")
    print("🌱 Loaded .env.local.local (development environment)")
elif os.path.exists(".env.local.prod"):
    load_dotenv(".env.local.prod")
    print("🚀 Loaded .env.local.prod (production environment)")
else:
    load_dotenv()
    print("⚙️ Loaded default .env.local")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    print("✅ Using DATABASE_URL from environment")
elif SUPABASE_URL and SUPABASE_KEY:
    print("✅ Using Supabase inferred configuration")
else:
    DATABASE_URL = "sqlite:///data/app.db"
    print("💾 No Supabase config found → using local SQLite fallback")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    future=True,
)

class Base(DeclarativeBase):
    """Classe de base pour les modèles SQLAlchemy"""
    pass

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
