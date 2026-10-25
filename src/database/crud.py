# ============= src/database/crud.py =============
from sqlalchemy.orm import Session
from src.database.models import User, Project, IrrigationEvent
from typing import List, Optional

class UserCRUD:
    @staticmethod
    def create_user(db: Session, username: str, email: str, hashed_password: str, role: str = "farmer") -> User:
        user = User(username=username, email=email, hashed_password=hashed_password, role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

class ProjectCRUD:
    @staticmethod
    def create_project(db: Session, user_id: int, **kwargs) -> Project:
        project = Project(user_id=user_id, **kwargs)
        db.add(project)
        db.commit()
        db.refresh(project)
        return project
    
    @staticmethod
    def get_project(db: Session, project_id: int) -> Optional[Project]:
        return db.query(Project).filter(Project.id == project_id).first()
    
    @staticmethod
    def get_user_projects(db: Session, user_id: int) -> List[Project]:
        return db.query(Project).filter(Project.user_id == user_id).all()
    
    @staticmethod
    def update_project(db: Session, project_id: int, **kwargs) -> Project:
        project = db.query(Project).filter(Project.id == project_id).first()
        for key, value in kwargs.items():
            setattr(project, key, value)
        db.commit()
        db.refresh(project)
        return project

class IrrigationEventCRUD:
    @staticmethod
    def create_event(db: Session, project_id: int, **kwargs) -> IrrigationEvent:
        event = IrrigationEvent(project_id=project_id, **kwargs)
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    
    @staticmethod
    def get_project_events(db: Session, project_id: int) -> List[IrrigationEvent]:
        return db.query(IrrigationEvent).filter(IrrigationEvent.project_id == project_id).all()