# function_calling.py
# Intelligent function calling system for MCP demo

import re
import json
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass

logger = logging.getLogger("function_calling")

@dataclass
class FunctionCall:
    """Represents a detected function call with parameters."""
    function_name: str
    parameters: Dict[str, Any]
    confidence: float = 1.0

@dataclass
class FunctionResult:
    """Represents the result of a function execution."""
    function_name: str
    parameters: Dict[str, Any]
    result: Any
    success: bool
    error: Optional[str] = None

class FunctionDetector:
    """Detects function calls from natural language input."""
    
    def __init__(self):
        # Define patterns for different function intents
        self.patterns = {
            'create_user': [
                r'create\s+(?:a\s+)?(?:new\s+)?user.*?(?:id|ID)\s*[:\s]*([^\s,]+).*?name\s*[:\s]*([^.,!?]+)',
                r'add\s+(?:a\s+)?(?:new\s+)?user.*?(?:id|ID)\s*[:\s]*([^\s,]+).*?name\s*[:\s]*([^.,!?]+)',
                r'new\s+user.*?(?:id|ID)\s*[:\s]*([^\s,]+).*?name\s*[:\s]*([^.,!?]+)',
                r'make\s+(?:a\s+)?user.*?(?:id|ID)\s*[:\s]*([^\s,]+).*?name\s*[:\s]*([^.,!?]+)',
            ],
            'get_user': [
                r'get\s+user.*?(?:id|ID)\s*[:\s]*([^\s,]+)',
                r'find\s+user.*?(?:id|ID)\s*[:\s]*([^\s,]+)',
                r'retrieve\s+user.*?(?:id|ID)\s*[:\s]*([^\s,]+)',
                r'show\s+user.*?(?:id|ID)\s*[:\s]*([^\s,]+)',
                r'lookup\s+user.*?(?:id|ID)\s*[:\s]*([^\s,]+)',
            ]
        }
    
    def detect_functions(self, text: str) -> List[FunctionCall]:
        """Detect function calls from natural language text."""
        detected_calls = []
        text_lower = text.lower()
        
        # Check for create_user patterns
        for pattern in self.patterns['create_user']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                user_id = match.group(1).strip()
                name = match.group(2).strip()
                # Clean up the name (remove quotes, extra spaces)
                name = re.sub(r'^["\']|["\']$', '', name).strip()
                
                detected_calls.append(FunctionCall(
                    function_name='create_user',
                    parameters={'user_id': user_id, 'name': name},
                    confidence=0.9
                ))
                logger.info(f"Detected create_user: user_id={user_id}, name={name}")
                break
        
        # Check for get_user patterns
        for pattern in self.patterns['get_user']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                user_id = match.group(1).strip()
                
                detected_calls.append(FunctionCall(
                    function_name='get_user',
                    parameters={'user_id': user_id},
                    confidence=0.9
                ))
                logger.info(f"Detected get_user: user_id={user_id}")
                break
        
        return detected_calls

class FunctionRegistry:
    """Registry for managing and executing functions."""
    
    def __init__(self):
        self.functions: Dict[str, Callable] = {}
        self.function_schemas: Dict[str, Dict] = {}
    
    def register_function(self, name: str, func: Callable, schema: Dict):
        """Register a function with its schema."""
        self.functions[name] = func
        self.function_schemas[name] = schema
        logger.info(f"Registered function: {name}")
    
    def execute_function(self, function_call: FunctionCall) -> FunctionResult:
        """Execute a function call and return the result."""
        func_name = function_call.function_name
        
        if func_name not in self.functions:
            return FunctionResult(
                function_name=func_name,
                parameters=function_call.parameters,
                result=None,
                success=False,
                error=f"Function '{func_name}' not found"
            )
        
        try:
            # Execute the function
            func = self.functions[func_name]
            result = func(**function_call.parameters)
            
            return FunctionResult(
                function_name=func_name,
                parameters=function_call.parameters,
                result=result,
                success=True
            )
        
        except Exception as e:
            logger.error(f"Error executing {func_name}: {str(e)}")
            return FunctionResult(
                function_name=func_name,
                parameters=function_call.parameters,
                result=None,
                success=False,
                error=str(e)
            )

class FunctionCallingSystem:
    """Main system that combines detection and execution."""
    
    def __init__(self):
        self.detector = FunctionDetector()
        self.registry = FunctionRegistry()
    
    def register_function(self, name: str, func: Callable, schema: Dict):
        """Register a function for calling."""
        self.registry.register_function(name, func, schema)
    
    def process_message(self, message: str) -> List[FunctionResult]:
        """Process a message and execute any detected function calls."""
        # Detect function calls
        detected_calls = self.detector.detect_functions(message)
        
        # Execute detected calls
        results = []
        for call in detected_calls:
            result = self.registry.execute_function(call)
            results.append(result)
        
        return results
