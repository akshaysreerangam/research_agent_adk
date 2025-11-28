# session/in_memory_session.py
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

class InMemorySessionManager:
    """
    Simple in-memory session manager for tracking sessions across agents.
    Can be integrated for shared memory in future extensions.
    """
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # Track sessions per user

    async def create_session(self, user_id: str, app_name: str = "default") -> 'Session':
        loop_time = asyncio.get_event_loop().time()
        session_id = f"{user_id}_{app_name}_{int(loop_time * 1000)}"
        created_at = datetime.now().isoformat()
        self.sessions[session_id] = {
            "user_id": user_id,
            "app_name": app_name,
            "memory": [],  # List of messages for conversation history
            "created_at": created_at,
            "metadata": {}
        }
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session_id)
        return Session(session_id, self)

    def add_to_memory(self, session_id: str, content: str, role: str = "assistant"):
        if session_id in self.sessions:
            self.sessions[session_id]["memory"].append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })

    def get_memory(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        memory = self.sessions.get(session_id, {}).get("memory", [])
        return memory[-limit:] if len(memory) > limit else memory

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.sessions.get(session_id)

    def list_user_sessions(self, user_id: str) -> List[str]:
        return self.user_sessions.get(user_id, [])

class Session:
    def __init__(self, id: str, manager: InMemorySessionManager):
        self.id = id
        self.manager = manager

    def add_message(self, content: str, role: str = "assistant"):
        self.manager.add_to_memory(self.id, content, role)

    def get_history(self, limit: int = 10) -> List[Dict[str, str]]:
        return self.manager.get_memory(self.id, limit)