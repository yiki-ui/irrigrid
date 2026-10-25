#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Chat Manager Service
Handles AI chat interactions with context and history
"""

import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.database.chat_history import ChatSession, ChatMessage
from config.database import SessionLocal


class ChatManager:
    """Manages AI chat sessions and history"""
    
    def __init__(self, db: Session = None):
        """Initialize chat manager with database session"""
        self.db = db or SessionLocal()
        self.current_session_id = None
        self.context_window = 10  # Number of messages to include in context
    
    def create_session(self, session_name: str = None, project_id: int = None) -> int:
        """
        Create a new chat session
        
        Args:
            session_name: Optional name for the session
            project_id: Optional associated project ID
            
        Returns:
            Session ID
        """
        if not session_name:
            session_name = f"Chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = ChatSession(
            session_name=session_name,
            project_id=project_id
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        self.current_session_id = session.id
        return session.id
    
    def get_or_create_session(self, project_id: int = None) -> int:
        """
        Get active session or create new one
        
        Args:
            project_id: Optional project ID
            
        Returns:
            Session ID
        """
        if self.current_session_id:
            # Check if session still active
            session = self.db.query(ChatSession).filter(
                ChatSession.id == self.current_session_id,
                ChatSession.is_active == 1
            ).first()
            
            if session:
                return self.current_session_id
        
        # Create new session
        return self.create_session(project_id=project_id)
    
    def add_message(
        self,
        role: str,
        content: str,
        context_data: Dict = None,
        model: str = None,
        tokens_used: int = None,
        response_time: int = None,
        session_id: int = None
    ) -> int:
        """
        Add a message to the chat history
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
            context_data: Current application context (JSON)
            model: AI model name
            tokens_used: Token count
            response_time: Response time in milliseconds
            session_id: Optional session ID (uses current if None)
            
        Returns:
            Message ID
        """
        if not session_id:
            session_id = self.get_or_create_session()
        
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            context_data=context_data,
            model=model,
            tokens_used=tokens_used,
            response_time=response_time
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        # Update session timestamp
        session = self.db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()
        if session:
            session.updated_at = datetime.utcnow()
            self.db.commit()
        
        return message.id
    
    def get_conversation_history(
        self,
        session_id: int = None,
        limit: int = None
    ) -> List[Dict]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session ID (uses current if None)
            limit: Maximum number of messages (newest first)
            
        Returns:
            List of messages
        """
        if not session_id:
            session_id = self.current_session_id
        
        if not session_id:
            return []
        
        query = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        messages = query.all()
        messages.reverse()  # Oldest first
        
        return [
            {
                'id': msg.id,
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'context_data': msg.context_data,
                'model': msg.model,
                'tokens_used': msg.tokens_used,
                'response_time': msg.response_time
            }
            for msg in messages
        ]
    
    def get_context_for_ai(self, session_id: int = None) -> List[Dict]:
        """
        Get recent conversation context for AI
        
        Args:
            session_id: Session ID (uses current if None)
            
        Returns:
            List of messages in Groq API format
        """
        history = self.get_conversation_history(
            session_id=session_id,
            limit=self.context_window
        )
        
        # Convert to Groq API format
        return [
            {
                'role': msg['role'],
                'content': msg['content']
            }
            for msg in history
        ]
    
    def search_messages(
        self,
        query: str,
        session_id: int = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search messages by content
        
        Args:
            query: Search query
            session_id: Optional session ID to search within
            limit: Maximum results
            
        Returns:
            List of matching messages
        """
        q = self.db.query(ChatMessage).filter(
            ChatMessage.content.like(f'%{query}%')
        )
        
        if session_id:
            q = q.filter(ChatMessage.session_id == session_id)
        
        messages = q.order_by(
            ChatMessage.timestamp.desc()
        ).limit(limit).all()
        
        return [
            {
                'id': msg.id,
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'session_id': msg.session_id
            }
            for msg in messages
        ]
    
    def rate_message(self, message_id: int, rating: int, is_helpful: bool = None):
        """
        Rate an AI response
        
        Args:
            message_id: Message ID
            rating: 1-5 stars
            is_helpful: Optional boolean feedback
        """
        message = self.db.query(ChatMessage).filter(
            ChatMessage.id == message_id
        ).first()
        
        if message:
            message.user_rating = rating
            if is_helpful is not None:
                message.is_helpful = 1 if is_helpful else 0
            self.db.commit()
    
    def get_all_sessions(self, include_archived: bool = False) -> List[Dict]:
        """
        Get all chat sessions
        
        Args:
            include_archived: Include archived sessions
            
        Returns:
            List of sessions
        """
        query = self.db.query(ChatSession)
        
        if not include_archived:
            query = query.filter(ChatSession.is_active == 1)
        
        sessions = query.order_by(
            ChatSession.updated_at.desc()
        ).all()
        
        return [
            {
                'id': s.id,
                'name': s.session_name,
                'project_id': s.project_id,
                'created_at': s.created_at.isoformat(),
                'updated_at': s.updated_at.isoformat(),
                'message_count': len(s.messages),
                'is_active': s.is_active
            }
            for s in sessions
        ]
    
    def archive_session(self, session_id: int):
        """Archive a session"""
        session = self.db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()
        
        if session:
            session.is_active = 0
            self.db.commit()
    
    def delete_session(self, session_id: int):
        """Permanently delete a session and all its messages"""
        session = self.db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()
        
        if session:
            self.db.delete(session)
            self.db.commit()
    
    def export_session(self, session_id: int, file_path: str):
        """
        Export session to JSON file
        
        Args:
            session_id: Session ID
            file_path: Output file path
        """
        session = self.db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        export_data = {
            'session': {
                'id': session.id,
                'name': session.session_name,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat()
            },
            'messages': [
                {
                    'timestamp': msg.timestamp.isoformat(),
                    'role': msg.role,
                    'content': msg.content,
                    'context_data': msg.context_data
                }
                for msg in session.messages
            ]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def get_statistics(self) -> Dict:
        """Get chat usage statistics"""
        total_sessions = self.db.query(ChatSession).count()
        active_sessions = self.db.query(ChatSession).filter(
            ChatSession.is_active == 1
        ).count()
        total_messages = self.db.query(ChatMessage).count()
        
        # Average response time
        avg_response = self.db.query(
            ChatMessage.response_time
        ).filter(
            ChatMessage.response_time.isnot(None)
        ).all()
        
        avg_response_time = sum(r[0] for r in avg_response) / len(avg_response) if avg_response else 0
        
        # Total tokens
        total_tokens = self.db.query(
            ChatMessage.tokens_used
        ).filter(
            ChatMessage.tokens_used.isnot(None)
        ).all()
        
        total_token_count = sum(t[0] for t in total_tokens) if total_tokens else 0
        
        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'total_messages': total_messages,
            'avg_response_time_ms': round(avg_response_time, 2),
            'total_tokens_used': total_token_count
        }
    
    def cleanup_old_sessions(self, days: int = 90):
        """
        Delete sessions older than specified days
        
        Args:
            days: Sessions older than this will be deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_sessions = self.db.query(ChatSession).filter(
            ChatSession.updated_at < cutoff_date,
            ChatSession.is_active == 0  # Only delete archived
        ).all()
        
        count = len(old_sessions)
        
        for session in old_sessions:
            self.db.delete(session)
        
        self.db.commit()
        
        return count
    
    def close(self):
        """Close database session"""
        self.db.close()


# Example usage
if __name__ == "__main__":
    # Test chat manager
    manager = ChatManager()
    
    print("=" * 60)
    print("CHAT MANAGER TEST")
    print("=" * 60)
    print()
    
    # Create session
    session_id = manager.create_session("Test Session")
    print(f"✓ Created session: {session_id}")
    
    # Add messages
    manager.add_message("user", "How do I calculate irrigation for tomatoes?")
    manager.add_message("assistant", "For tomatoes, use Kc values: 0.6 (initial), 1.15 (mid), 0.8 (end)...")
    manager.add_message("user", "What about soil type?")
    print("✓ Added 3 messages")
    
    # Get history
    history = manager.get_conversation_history()
    print(f"✓ Retrieved {len(history)} messages")
    
    # Get AI context
    context = manager.get_context_for_ai()
    print(f"✓ AI context: {len(context)} messages")
    
    # Statistics
    stats = manager.get_statistics()
    print(f"✓ Statistics: {stats}")
    
    manager.close()
    print("\n✓ Test complete!")
