#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI Chat History Database Module
Stores conversation history with Groq AI for context and learning
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class ChatSession(Base):
    """Chat session model - groups related conversations"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_name = Column(String(200), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Integer, default=1)  # 0=archived, 1=active
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    project = relationship("Project", back_populates="chat_sessions")


class ChatMessage(Base):
    """Individual chat message model"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # Context data (JSON): current tab, selected location, crop, etc.
    context_data = Column(JSON, nullable=True)
    
    # AI metadata
    model = Column(String(50), nullable=True)  # e.g., "mixtral-8x7b-32768"
    tokens_used = Column(Integer, nullable=True)
    response_time = Column(Integer, nullable=True)  # milliseconds
    
    # Feedback
    user_rating = Column(Integer, nullable=True)  # 1-5 stars
    is_helpful = Column(Integer, nullable=True)  # 0=no, 1=yes
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")


# Update Project model to include chat sessions relationship
# This will be done in the main models.py file
