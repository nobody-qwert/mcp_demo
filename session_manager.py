# session_manager.py
# Session management for MCP WebSocket connections

import asyncio
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger("session_manager")

@dataclass
class MCPSession:
    """Represents an active MCP session."""
    session_id: str
    websocket: WebSocketServerProtocol
    protocol_version: str = "2024-11-05"
    capabilities: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    initialized: bool = False

class SessionManager:
    """Manages WebSocket sessions for MCP connections."""
    
    def __init__(self):
        self.sessions: Dict[str, MCPSession] = {}
        self.websocket_to_session: Dict[WebSocketServerProtocol, str] = {}
    
    def create_session(self, websocket: WebSocketServerProtocol) -> MCPSession:
        """Create a new session for a WebSocket connection."""
        session_id = str(uuid.uuid4())
        session = MCPSession(
            session_id=session_id,
            websocket=websocket
        )
        
        self.sessions[session_id] = session
        self.websocket_to_session[websocket] = session_id
        
        logger.info(f"Created new session: {session_id}")
        return session
    
    def get_session(self, websocket: WebSocketServerProtocol) -> Optional[MCPSession]:
        """Get session by WebSocket connection."""
        session_id = self.websocket_to_session.get(websocket)
        if session_id:
            return self.sessions.get(session_id)
        return None
    
    def get_session_by_id(self, session_id: str) -> Optional[MCPSession]:
        """Get session by session ID."""
        return self.sessions.get(session_id)
    
    def remove_session(self, websocket: WebSocketServerProtocol):
        """Remove a session when WebSocket disconnects."""
        session_id = self.websocket_to_session.get(websocket)
        if session_id:
            del self.websocket_to_session[websocket]
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Removed session: {session_id}")
    
    def update_session_context(self, session_id: str, key: str, value: Any):
        """Update session context."""
        session = self.sessions.get(session_id)
        if session:
            session.context[key] = value
    
    def get_active_sessions(self) -> Dict[str, MCPSession]:
        """Get all active sessions."""
        return self.sessions.copy()
    
    async def broadcast_to_all(self, message: str):
        """Broadcast a message to all active sessions."""
        if not self.sessions:
            return
        
        disconnected = []
        for session_id, session in self.sessions.items():
            try:
                await session.websocket.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(session.websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to session {session_id}: {e}")
                disconnected.append(session.websocket)
        
        # Clean up disconnected sessions
        for websocket in disconnected:
            self.remove_session(websocket)
