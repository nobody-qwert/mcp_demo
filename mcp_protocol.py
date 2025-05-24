# mcp_protocol.py
# MCP protocol implementation with JSON-RPC 2.0

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import uuid

logger = logging.getLogger("mcp_protocol")

# MCP Error Codes
class MCPErrorCodes:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # MCP-specific error codes
    TOOL_NOT_FOUND = -32000
    TOOL_EXECUTION_ERROR = -32001
    SESSION_NOT_INITIALIZED = -32002
    CONSENT_REQUIRED = -32003

@dataclass
class JSONRPCRequest:
    """JSON-RPC 2.0 request structure."""
    jsonrpc: str
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

@dataclass
class JSONRPCResponse:
    """JSON-RPC 2.0 response structure."""
    jsonrpc: str
    id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

@dataclass
class JSONRPCError:
    """JSON-RPC 2.0 error structure."""
    code: int
    message: str
    data: Optional[Any] = None

class MCPProtocolHandler:
    """Handles MCP protocol messages and routing."""
    
    def __init__(self, session_manager, tool_registry, llm_integration=None):
        self.session_manager = session_manager
        self.tool_registry = tool_registry
        self.llm_integration = llm_integration
        self.pending_requests: Dict[str, asyncio.Future] = {}
    
    def parse_message(self, message: str) -> JSONRPCRequest:
        """Parse incoming JSON-RPC message."""
        try:
            data = json.loads(message)
        except json.JSONDecodeError as e:
            raise self.create_error(MCPErrorCodes.PARSE_ERROR, "Parse error", str(e))
        
        # Validate JSON-RPC structure
        if data.get("jsonrpc") != "2.0":
            raise self.create_error(MCPErrorCodes.INVALID_REQUEST, "Invalid JSON-RPC version")
        
        if "method" not in data:
            raise self.create_error(MCPErrorCodes.INVALID_REQUEST, "Missing method")
        
        return JSONRPCRequest(
            jsonrpc=data["jsonrpc"],
            method=data["method"],
            params=data.get("params"),
            id=data.get("id")
        )
    
    def create_response(self, request_id: Optional[str], result: Any = None, error: Optional[JSONRPCError] = None) -> str:
        """Create JSON-RPC response."""
        response = JSONRPCResponse(
            jsonrpc="2.0",
            id=request_id,
            result=result,
            error=error.__dict__ if error else None
        )
        
        response_dict = {
            "jsonrpc": response.jsonrpc,
            "id": response.id
        }
        
        if error:
            response_dict["error"] = response.error
        else:
            response_dict["result"] = response.result
        
        return json.dumps(response_dict)
    
    def create_notification(self, method: str, params: Dict[str, Any]) -> str:
        """Create JSON-RPC notification (no response expected)."""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        return json.dumps(notification)
    
    def create_error(self, code: int, message: str, data: Any = None) -> JSONRPCError:
        """Create JSON-RPC error."""
        return JSONRPCError(code=code, message=message, data=data)
    
    async def handle_message(self, websocket, message: str) -> Optional[str]:
        """Handle incoming MCP message."""
        try:
            request = self.parse_message(message)
            session = self.session_manager.get_session(websocket)
            
            if not session:
                error = self.create_error(MCPErrorCodes.INTERNAL_ERROR, "Session not found")
                return self.create_response(request.id, error=error)
            
            # Route to appropriate handler
            handler_method = f"handle_{request.method.replace('.', '_')}"
            if hasattr(self, handler_method):
                handler = getattr(self, handler_method)
                result = await handler(session, request.params or {})
                return self.create_response(request.id, result=result)
            else:
                error = self.create_error(MCPErrorCodes.METHOD_NOT_FOUND, f"Method '{request.method}' not found")
                return self.create_response(request.id, error=error)
        
        except JSONRPCError as e:
            return self.create_response(getattr(request, 'id', None) if 'request' in locals() else None, error=e)
        except Exception as e:
            logger.error(f"Unexpected error handling message: {e}")
            error = self.create_error(MCPErrorCodes.INTERNAL_ERROR, "Internal server error", str(e))
            return self.create_response(getattr(request, 'id', None) if 'request' in locals() else None, error=error)
    
    async def handle_mcp_initialize(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle mcp.initialize request."""
        client_version = params.get("protocolVersion", "2024-11-05")
        client_capabilities = params.get("capabilities", {})
        
        # Update session
        session.protocol_version = client_version
        session.capabilities = client_capabilities
        session.initialized = True
        
        logger.info(f"Initialized session {session.session_id} with protocol version {client_version}")
        
        return {
            "protocolVersion": "2024-11-05",
            "sessionId": session.session_id,
            "capabilities": {
                "tools": True,
                "streaming": True,
                "progress": True,
                "consent": True
            },
            "serverInfo": {
                "name": "MCP Demo Server",
                "version": "1.0.0"
            }
        }
    
    async def handle_mcp_ping(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle mcp.ping request (heartbeat)."""
        return {"pong": True, "timestamp": params.get("timestamp")}
    
    async def handle_mcp_cancel(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle mcp.cancel request."""
        request_id = params.get("requestId")
        if request_id and request_id in self.pending_requests:
            future = self.pending_requests[request_id]
            future.cancel()
            del self.pending_requests[request_id]
            return {"cancelled": True, "requestId": request_id}
        return {"cancelled": False, "requestId": request_id}
    
    async def handle_tools_list(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools.list request."""
        if not session.initialized:
            raise self.create_error(MCPErrorCodes.SESSION_NOT_INITIALIZED, "Session not initialized")
        
        tools = self.tool_registry.list_tools()
        return {"tools": tools}
    
    async def handle_tool_invoke(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool.invoke request."""
        if not session.initialized:
            raise self.create_error(MCPErrorCodes.SESSION_NOT_INITIALIZED, "Session not initialized")
        
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            raise self.create_error(MCPErrorCodes.INVALID_PARAMS, "Missing tool name")
        
        # Check if consent is required (for demo, we'll require consent for all tools)
        consent_granted = await self.request_consent(session, tool_name, arguments)
        if not consent_granted:
            raise self.create_error(MCPErrorCodes.CONSENT_REQUIRED, "User consent required")
        
        try:
            result = await self.tool_registry.invoke_tool(tool_name, arguments)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Tool '{tool_name}' executed successfully"
                    }
                ],
                "result": result,
                "isError": False
            }
        except ValueError as e:
            raise self.create_error(MCPErrorCodes.TOOL_NOT_FOUND, str(e))
        except Exception as e:
            raise self.create_error(MCPErrorCodes.TOOL_EXECUTION_ERROR, str(e))
    
    async def request_consent(self, session, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Request user consent for tool execution."""
        # Send consent notification
        consent_notification = self.create_notification("user.consent", {
            "tool": tool_name,
            "arguments": arguments,
            "message": f"Do you want to execute tool '{tool_name}' with the provided arguments?"
        })
        
        try:
            await session.websocket.send(consent_notification)
            # For demo purposes, we'll assume consent is granted
            # In a real implementation, you'd wait for a consent response
            logger.info(f"Consent requested for tool {tool_name} in session {session.session_id}")
            return True
        except Exception as e:
            logger.error(f"Error requesting consent: {e}")
            return False
    
    async def send_progress(self, session, request_id: str, progress: float, message: str):
        """Send progress notification."""
        progress_notification = self.create_notification("tool.progress", {
            "requestId": request_id,
            "progress": progress,
            "message": message
        })
        
        try:
            await session.websocket.send(progress_notification)
        except Exception as e:
            logger.error(f"Error sending progress: {e}")
    
    async def send_stream(self, session, request_id: str, content: str, done: bool = False):
        """Send streaming content notification."""
        stream_notification = self.create_notification("stream", {
            "requestId": request_id,
            "content": content,
            "done": done
        })
        
        try:
            await session.websocket.send(stream_notification)
        except Exception as e:
            logger.error(f"Error sending stream: {e}")
