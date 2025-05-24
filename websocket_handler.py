# websocket_handler.py
# WebSocket server for MCP protocol

import asyncio
import logging
import websockets
from websockets.server import WebSocketServerProtocol
from typing import Set
import signal
import sys

from session_manager import SessionManager
from tool_registry import MCPToolRegistry, create_default_registry
from mcp_protocol import MCPProtocolHandler
from llm_integration import StreamingLLMIntegration, MockLLMIntegration
from dummy_app import MockApp

logger = logging.getLogger("websocket_handler")

class MCPWebSocketServer:
    """WebSocket server for MCP protocol."""
    
    def __init__(self, host: str = "localhost", port: int = 8080, use_mock_llm: bool = False):
        self.host = host
        self.port = port
        self.use_mock_llm = use_mock_llm
        
        # Initialize components
        self.session_manager = SessionManager()
        self.mock_app = MockApp()
        self.tool_registry = create_default_registry(self.mock_app)
        
        # Initialize LLM integration
        if use_mock_llm:
            self.llm_integration = MockLLMIntegration()
        else:
            self.llm_integration = StreamingLLMIntegration()
        
        self.protocol_handler = MCPProtocolHandler(
            self.session_manager,
            self.tool_registry,
            self.llm_integration
        )
        
        self.server = None
        self.running = False
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str = "/"):
        """Handle a new WebSocket client connection."""
        session = self.session_manager.create_session(websocket)
        logger.info(f"New client connected: {session.session_id} from {websocket.remote_address}")
        
        try:
            async for message in websocket:
                try:
                    logger.debug(f"Received message from {session.session_id}: {message}")
                    
                    # Handle the message through the protocol handler
                    response = await self.protocol_handler.handle_message(websocket, message)
                    
                    if response:
                        await websocket.send(response)
                        logger.debug(f"Sent response to {session.session_id}: {response}")
                
                except Exception as e:
                    logger.error(f"Error handling message from {session.session_id}: {e}")
                    # Send error response
                    error_response = self.protocol_handler.create_response(
                        None,
                        error=self.protocol_handler.create_error(-32603, "Internal server error", str(e))
                    )
                    try:
                        await websocket.send(error_response)
                    except:
                        pass  # Connection might be closed
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {session.session_id} disconnected")
        except Exception as e:
            logger.error(f"Unexpected error with client {session.session_id}: {e}")
        finally:
            # Clean up session
            self.session_manager.remove_session(websocket)
    
    async def start_server(self):
        """Start the WebSocket server."""
        logger.info(f"Starting MCP WebSocket server on {self.host}:{self.port}")
        
        # Initialize LLM if not using mock
        if not self.use_mock_llm:
            logger.info("Initializing LLM model...")
            await self.llm_integration.initialize()
            logger.info("LLM model initialized")
        
        # Start WebSocket server
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=30,  # Send ping every 30 seconds
            ping_timeout=10,   # Wait 10 seconds for pong
            close_timeout=10   # Wait 10 seconds for close
        )
        
        self.running = True
        logger.info(f"MCP WebSocket server started on ws://{self.host}:{self.port}")
        
        # Log registered tools
        tools = self.tool_registry.list_tools()
        logger.info(f"Registered {len(tools)} tools:")
        for tool in tools:
            logger.info(f"  - {tool['name']}: {tool['description']}")
    
    async def stop_server(self):
        """Stop the WebSocket server."""
        if self.server:
            logger.info("Stopping MCP WebSocket server...")
            self.server.close()
            await self.server.wait_closed()
            self.running = False
            logger.info("MCP WebSocket server stopped")
    
    async def run_forever(self):
        """Run the server until interrupted."""
        await self.start_server()
        
        # Set up signal handlers for graceful shutdown
        def signal_handler():
            logger.info("Received shutdown signal")
            asyncio.create_task(self.stop_server())
        
        if sys.platform != "win32":
            # Unix signal handling
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, signal_handler)
        
        try:
            # Keep the server running
            await self.server.wait_closed()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            await self.stop_server()
    
    def get_server_info(self) -> dict:
        """Get server information."""
        return {
            "host": self.host,
            "port": self.port,
            "running": self.running,
            "active_sessions": len(self.session_manager.get_active_sessions()),
            "registered_tools": len(self.tool_registry.tools),
            "llm_type": "mock" if self.use_mock_llm else "real"
        }

async def main():
    """Main entry point for the WebSocket server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run server
    server = MCPWebSocketServer(host="localhost", port=8080, use_mock_llm=False)
    
    try:
        await server.run_forever()
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        logger.info("Server shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
