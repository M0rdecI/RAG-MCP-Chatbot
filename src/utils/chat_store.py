# src/utils/chat_store.py
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    sources: Optional[List[Dict]] = None

class ChatStore:
    def __init__(self, storage_path: str = "data/chat_history"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.current_session = []
    
    def _get_session_file(self, session_id: str) -> Path:
        return self.storage_path / f"{session_id}.json"
    
    def add_message(self, session_id: str, message: ChatMessage):
        """Add a message to current session and persist to disk"""
        self.current_session.append(message.dict())
        
        session_file = self._get_session_file(session_id)
        try:
            if session_file.exists():
                with open(session_file, "r") as f:
                    history = json.load(f)
            else:
                history = []
            
            history.append(message.dict())
            
            with open(session_file, "w") as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"Error saving chat history: {e}")
    
    def get_session_history(self, session_id: str) -> List[ChatMessage]:
        """Retrieve full history for a session"""
        session_file = self._get_session_file(session_id)
        if not session_file.exists():
            return []
        
        try:
            with open(session_file, "r") as f:
                history = json.load(f)
            return [ChatMessage(**msg) for msg in history]
        except Exception as e:
            print(f"Error loading chat history: {e}")
            return []
    
    def clear_session(self, session_id: str):
        """Clear history for a specific session"""
        session_file = self._get_session_file(session_id)
        if session_file.exists():
            session_file.unlink()
        self.current_session = []