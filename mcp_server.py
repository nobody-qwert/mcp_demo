# mcp_server.py
# MCP-compliant WebSocket server with JSON-RPC 2.0
# Version: 2.0.0

import asyncio
import logging
import argparse
import sys
import os
from websocket_handler import MCPWebSocketServer

# Version information
def get_version():
    """Get version from VERSION file."""
    try:
        version_file = os.path.join(os.path.dirname(__file__), 'VERSION')
        with open(version_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "2.0.0"  # Fallback version

__version__ = get_version()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("mcp_server")

async def main():
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="MCP Demo Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--mock-llm", action="store_true", help="Use mock LLM for testing")
    
    args = parser.parse_args()
    
    logger.info(f"Starting MCP Demo Server v{__version__}")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Mock LLM: {args.mock_llm}")
    
    # Create and run the WebSocket server
    server = MCPWebSocketServer(
        host=args.host,
        port=args.port,
        use_mock_llm=args.mock_llm
    )
    
    try:
        await server.run_forever()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        logger.info("MCP server shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server interrupted")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
