# Changelog

All notable changes to the MCP Demo Server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-05-24

### 🚀 Major Release: Full MCP Protocol Compliance

This is a complete architectural refactoring from HTTP REST API to a fully MCP-compliant WebSocket server implementing JSON-RPC 2.0.

### Added

#### Core MCP Protocol Implementation
- **WebSocket Server**: Complete WebSocket-based server replacing HTTP endpoints
- **JSON-RPC 2.0**: Full specification compliance for all communication
- **Session Management**: Stateful connections with unique session IDs and lifecycle management
- **Capability Negotiation**: Protocol version discovery and feature negotiation during initialization

#### MCP Protocol Methods
- `mcp.initialize` - Session initialization with capability negotiation
- `mcp.ping` / `mcp.pong` - Heartbeat mechanism for connection health monitoring
- `mcp.cancel` - Request cancellation support
- `tools.list` - Tool discovery with JSON Schema metadata
- `tool.invoke` - Secure tool execution with parameter validation

#### Tool Registry & Validation
- **JSON Schema Integration**: Complete tool parameter validation using JSON Schema
- **Tool Discovery**: Dynamic tool registration and schema publication
- **Parameter Validation**: Automatic validation of all tool parameters before execution
- **Error Handling**: MCP-compliant error codes and structured error responses

#### Security & Consent
- **User Consent Mechanism**: `user.consent` notifications before tool execution
- **Secure Execution Environment**: Isolated tool execution with proper error handling
- **Session Isolation**: Each WebSocket connection maintains separate session state

#### Real-time Communication
- **Bidirectional Messaging**: Full duplex WebSocket communication
- **Progress Notifications**: `tool.progress` updates for long-running operations
- **Streaming Support**: Infrastructure for streaming LLM responses
- **Connection Management**: Automatic cleanup and session management

#### New Components
- `websocket_handler.py` - WebSocket server implementation with connection management
- `mcp_protocol.py` - JSON-RPC 2.0 and MCP protocol handler
- `session_manager.py` - Session lifecycle and state management
- `tool_registry.py` - JSON Schema-based tool registry with validation
- `llm_integration.py` - Streaming LLM integration with mock support
- `test_mcp_websocket.py` - Comprehensive WebSocket test client

#### Testing & Validation
- **Comprehensive Test Suite**: Complete MCP protocol validation
- **WebSocket Test Client**: Automated testing of all MCP features
- **Protocol Compliance**: Validation of JSON-RPC 2.0 and MCP specifications
- **Error Handling Tests**: Edge case and error condition testing

#### Documentation
- **Updated README**: Complete documentation rewrite with MCP protocol details
- **Architecture Diagrams**: Mermaid diagrams showing MCP protocol flow and component architecture
- **API Documentation**: Detailed MCP method documentation with examples
- **Migration Guide**: Documentation of changes from HTTP to WebSocket

### Changed

#### Architecture Transformation
- **Transport Protocol**: HTTP REST → WebSocket with JSON-RPC 2.0
- **Communication Model**: Request/Response → Bidirectional real-time messaging
- **Tool System**: Custom function detection → JSON Schema-based tool registry
- **Session Model**: Stateless → Stateful with session management
- **Error Handling**: Simple HTTP errors → MCP-compliant structured errors

#### Updated Files
- `mcp_server.py` - Refactored to use WebSocket server instead of FastAPI
- `requirements.txt` - Added WebSocket (`websockets`) and JSON Schema (`jsonschema`) dependencies
- `dummy_app.py` - Enhanced with better logging and error handling

### Preserved (Backward Compatibility)
- `function_calling.py` - Legacy intelligent function calling system (preserved for reference)
- `test_mcp.ps1` - Original HTTP test script (preserved for comparison)
- Core application logic in `dummy_app.py` - User management functions maintained

### Technical Improvements
- **Performance**: WebSocket connections eliminate HTTP overhead
- **Real-time**: Instant bidirectional communication
- **Scalability**: Session-based architecture supports multiple concurrent clients
- **Standards Compliance**: Full adherence to MCP and JSON-RPC 2.0 specifications
- **Extensibility**: Modular architecture for easy tool addition and customization

### Dependencies
- Added `websockets>=12.0` for WebSocket server implementation
- Added `jsonschema>=4.0.0` for JSON Schema validation
- Maintained existing dependencies for LLM integration

### Breaking Changes
- **API Endpoints**: All HTTP endpoints removed in favor of WebSocket JSON-RPC methods
- **Client Integration**: Clients must now use WebSocket connections instead of HTTP requests
- **Message Format**: All communication now uses JSON-RPC 2.0 format
- **Authentication**: Session-based authentication replaces stateless HTTP

### Migration Notes
- Clients need to implement WebSocket connection and JSON-RPC 2.0 protocol
- Tool invocation now requires proper JSON Schema parameter validation
- Session initialization required before any tool operations
- Error handling updated to use MCP-compliant error codes

---

## [1.0.0] - 2025-05-24 (Pre-MCP Legacy Version)

### Initial Release - HTTP REST API with Intelligent Function Calling

#### Added
- **FastAPI Server**: HTTP REST API with `/ask`, `/tools/create_user`, `/tools/get_user` endpoints
- **Intelligent Function Calling**: Regex-based intent detection from natural language
- **LLM Integration**: DistilGPT-2 model integration with streaming support
- **Mock Application**: User management system with create/get operations
- **Function Detection**: Pattern-based detection of user intents
- **Basic Error Handling**: HTTP status codes and error responses

#### Core Components
- `mcp_server.py` - FastAPI application with HTTP endpoints
- `function_calling.py` - Intelligent function calling system with regex patterns
- `dummy_app.py` - Mock user management application
- `test_mcp.ps1` - PowerShell test script for HTTP endpoints

#### Features
- Natural language processing for function detection
- Automatic parameter extraction from user messages
- LLM response generation and combination with function results
- Mock LLM support for testing
- Comprehensive logging and error handling

#### Dependencies
- FastAPI for HTTP server
- Transformers for LLM integration
- Torch for model execution
- Pydantic for data validation

---

## Version Numbering Scheme

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version (X.0.0): Incompatible API changes
- **MINOR** version (0.X.0): Backward-compatible functionality additions
- **PATCH** version (0.0.X): Backward-compatible bug fixes

### Version History Summary
- **v2.0.0**: Full MCP protocol compliance with WebSocket JSON-RPC 2.0
- **v1.0.0**: Initial HTTP REST API with intelligent function calling
