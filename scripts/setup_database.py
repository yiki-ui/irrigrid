# ============= scripts/setup_database.py =============
"""
Initialize database with sample data
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import engine, Base, SessionLocal
from src.database.models import User, Project

# Import chat history models to register them with Base
try:
    from src.database.chat_history import ChatSession, ChatMessage
    print("[OK] Chat history models imported")
except ImportError as e:
    print(f"[WARNING] Chat history models not available: {e}")

try:
    from passlib.hash import bcrypt
    PASSLIB_AVAILABLE = True
except ImportError:
    PASSLIB_AVAILABLE = False
    print("[WARNING] passlib not installed - password hashing disabled")

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("[OK] Tables created successfully!")
    print(f"  Tables: {', '.join(Base.metadata.tables.keys())}")

def create_demo_user():
    """Create demo user account"""
    if not PASSLIB_AVAILABLE:
        print("[SKIP] Skipping demo user creation (passlib not installed)")
        return
    
    db = SessionLocal()
    
    try:
        # Check if demo user exists
        existing = db.query(User).filter(User.username == "demo").first()
        if existing:
            print("[OK] Demo user already exists")
            return
        
        # Create demo user
        hashed_password = bcrypt.hash("demo123")
        demo_user = User(
            username="demo",
            email="demo@example.com",
            hashed_password=hashed_password,
            role="farmer"
        )
        
        db.add(demo_user)
        db.commit()
        print("[OK] Demo user created (username: demo, password: demo123)")
        
    except Exception as e:
        print(f"[ERROR] Error creating demo user: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    print("=" * 60)
    print("Database Setup")
    print("=" * 60)
    
    create_tables()
    create_demo_user()
    
    print("\n[OK] Database setup complete!")
    print("\nYou can now run: python main.py")

if __name__ == "__main__":
    main()
