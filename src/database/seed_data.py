# ============= src/database/seed_data.py =============
from sqlalchemy.orm import Session
from src.database.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_initial_data(db: Session):
    """Seed database with initial data"""
    
    # Check if admin user exists
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@irrigation-dss.rw",
            hashed_password=pwd_context.hash("Admin@123"),
            role="admin"
        )
        db.add(admin)
    
    # Create demo farmer
    demo_farmer = db.query(User).filter(User.username == "demo_farmer").first()
    if not demo_farmer:
        demo_farmer = User(
            username="demo_farmer",
            email="farmer@demo.rw",
            hashed_password=pwd_context.hash("Farmer@123"),
            role="farmer"
        )
        db.add(demo_farmer)
    
    db.commit()
    print("Database seeded successfully!")
    print("Admin credentials: admin / Admin@123")
    print("Demo farmer credentials: demo_farmer / Farmer@123")
