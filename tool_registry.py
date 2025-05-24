# tool_registry.py
# MCP-compliant tool registry with JSON Schema support

import json
import logging
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
import jsonschema
from jsonschema import validate, ValidationError

logger = logging.getLogger("tool_registry")

@dataclass
class MCPTool:
    """Represents an MCP tool with schema and handler."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to MCP tool definition format."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }

class MCPToolRegistry:
    """Registry for MCP tools with JSON Schema validation."""
    
    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
    
    def register_tool(self, name: str, description: str, input_schema: Dict[str, Any], handler: Callable):
        """Register a new tool with JSON Schema validation."""
        # Validate the schema itself
        try:
            jsonschema.Draft7Validator.check_schema(input_schema)
        except jsonschema.SchemaError as e:
            logger.error(f"Invalid schema for tool {name}: {e}")
            raise ValueError(f"Invalid schema for tool {name}: {e}")
        
        tool = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler
        )
        
        self.tools[name] = tool
        logger.info(f"Registered MCP tool: {name}")
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools in MCP format."""
        return [tool.to_dict() for tool in self.tools.values()]
    
    def validate_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> bool:
        """Validate parameters against tool schema."""
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        try:
            validate(instance=parameters, schema=tool.input_schema)
            return True
        except ValidationError as e:
            logger.error(f"Parameter validation failed for {tool_name}: {e}")
            raise ValueError(f"Parameter validation failed: {e.message}")
    
    async def invoke_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Invoke a tool with validated parameters."""
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        # Validate parameters
        self.validate_parameters(tool_name, parameters)
        
        try:
            # Execute the tool handler
            result = tool.handler(**parameters)
            logger.info(f"Successfully executed tool {tool_name}")
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            raise RuntimeError(f"Tool execution failed: {str(e)}")

# Predefined schemas for common tools
USER_MANAGEMENT_SCHEMAS = {
    "create_user": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "Unique identifier for the user",
                "minLength": 1
            },
            "name": {
                "type": "string",
                "description": "Display name for the user",
                "minLength": 1
            }
        },
        "required": ["user_id", "name"],
        "additionalProperties": False
    },
    
    "get_user": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "Unique identifier for the user to retrieve",
                "minLength": 1
            }
        },
        "required": ["user_id"],
        "additionalProperties": False
    }
}

def create_default_registry(mock_app) -> MCPToolRegistry:
    """Create a registry with default tools for the mock app."""
    registry = MCPToolRegistry()
    
    # Register create_user tool
    registry.register_tool(
        name="create_user",
        description="Create a new user in the system with a unique ID and name",
        input_schema=USER_MANAGEMENT_SCHEMAS["create_user"],
        handler=mock_app.create_user
    )
    
    # Register get_user tool
    registry.register_tool(
        name="get_user",
        description="Retrieve user information by user ID",
        input_schema=USER_MANAGEMENT_SCHEMAS["get_user"],
        handler=mock_app.get_user
    )
    
    return registry
