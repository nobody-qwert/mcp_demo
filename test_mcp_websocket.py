# test_mcp_websocket.py
# WebSocket client for testing MCP server

import asyncio
import json
import logging
import websockets
from typing import Dict, Any
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_test_client")

class MCPTestClient:
    """Test client for MCP WebSocket server."""
    
    def __init__(self, uri: str = "ws://localhost:8080"):
        self.uri = uri
        self.websocket = None
        self.session_id = None
        self.request_counter = 0
    
    def create_request(self, method: str, params: Dict[str, Any] = None) -> str:
        """Create a JSON-RPC 2.0 request."""
        self.request_counter += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": f"req-{self.request_counter}"
        }
        if params:
            request["params"] = params
        
        return json.dumps(request)
    
    def create_notification(self, method: str, params: Dict[str, Any] = None) -> str:
        """Create a JSON-RPC 2.0 notification (no response expected)."""
        notification = {
            "jsonrpc": "2.0",
            "method": method
        }
        if params:
            notification["params"] = params
        
        return json.dumps(notification)
    
    async def connect(self):
        """Connect to the MCP server."""
        logger.info(f"Connecting to {self.uri}")
        self.websocket = await websockets.connect(self.uri)
        logger.info("Connected to MCP server")
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from MCP server")
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a request and wait for response."""
        request = self.create_request(method, params)
        logger.info(f"Sending request: {request}")
        
        await self.websocket.send(request)
        response = await self.websocket.recv()
        
        logger.info(f"Received response: {response}")
        return json.loads(response)
    
    async def send_notification(self, method: str, params: Dict[str, Any] = None):
        """Send a notification (no response expected)."""
        notification = self.create_notification(method, params)
        logger.info(f"Sending notification: {notification}")
        await self.websocket.send(notification)
    
    async def initialize_session(self) -> Dict[str, Any]:
        """Initialize MCP session."""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": True,
                "streaming": True
            },
            "clientInfo": {
                "name": "MCP Test Client",
                "version": "1.0.0"
            }
        }
        
        response = await self.send_request("mcp.initialize", params)
        
        if "result" in response:
            self.session_id = response["result"].get("sessionId")
            logger.info(f"Session initialized: {self.session_id}")
        
        return response
    
    async def ping(self) -> Dict[str, Any]:
        """Send ping request."""
        import time
        timestamp = int(time.time() * 1000)
        return await self.send_request("mcp.ping", {"timestamp": timestamp})
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        return await self.send_request("tools.list")
    
    async def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a tool."""
        params = {
            "name": tool_name,
            "arguments": arguments
        }
        return await self.send_request("tool.invoke", params)
    
    async def run_test_sequence(self):
        """Run a complete test sequence."""
        try:
            await self.connect()
            
            # Test 1: Initialize session
            logger.info("\n=== Test 1: Initialize Session ===")
            init_response = await self.initialize_session()
            assert "result" in init_response, "Initialization failed"
            assert "sessionId" in init_response["result"], "No session ID returned"
            
            # Test 2: Ping
            logger.info("\n=== Test 2: Ping ===")
            ping_response = await self.ping()
            assert "result" in ping_response, "Ping failed"
            assert ping_response["result"]["pong"] == True, "Invalid ping response"
            
            # Test 3: List tools
            logger.info("\n=== Test 3: List Tools ===")
            tools_response = await self.list_tools()
            assert "result" in tools_response, "List tools failed"
            tools = tools_response["result"]["tools"]
            logger.info(f"Available tools: {[tool['name'] for tool in tools]}")
            
            # Test 4: Create user
            logger.info("\n=== Test 4: Create User ===")
            create_response = await self.invoke_tool("create_user", {
                "user_id": "test123",
                "name": "Test User"
            })
            assert "result" in create_response, "Create user failed"
            logger.info(f"Create user result: {create_response['result']}")
            
            # Test 5: Get user
            logger.info("\n=== Test 5: Get User ===")
            get_response = await self.invoke_tool("get_user", {
                "user_id": "test123"
            })
            assert "result" in get_response, "Get user failed"
            logger.info(f"Get user result: {get_response['result']}")
            
            # Test 6: Error handling - invalid tool
            logger.info("\n=== Test 6: Error Handling ===")
            try:
                error_response = await self.invoke_tool("invalid_tool", {})
                logger.info(f"Error response: {error_response}")
                assert "error" in error_response, "Expected error response"
            except Exception as e:
                logger.info(f"Expected error occurred: {e}")
            
            logger.info("\n=== All Tests Passed! ===")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            raise
        finally:
            await self.disconnect()

async def main():
    """Main test function."""
    client = MCPTestClient()
    await client.run_test_sequence()

if __name__ == "__main__":
    asyncio.run(main())
