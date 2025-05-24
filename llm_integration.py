# llm_integration.py
# LLM integration with streaming support for MCP

import asyncio
import logging
import re
from typing import AsyncGenerator, Dict, Any, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch

logger = logging.getLogger("llm_integration")

class StreamingLLMIntegration:
    """LLM integration with streaming response support."""
    
    def __init__(self, model_name: str = "distilgpt2"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.is_loaded = False
    
    async def initialize(self):
        """Initialize the LLM model asynchronously."""
        if self.is_loaded:
            return
        
        logger.info(f"Loading LLM model: {self.model_name}")
        
        # Load model and tokenizer in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        
        def load_model():
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForCausalLM.from_pretrained(self.model_name)
            
            # Add padding token if it doesn't exist
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            pipe = pipeline(
                "text-generation", 
                model=model, 
                tokenizer=tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            return tokenizer, model, pipe
        
        self.tokenizer, self.model, self.pipeline = await loop.run_in_executor(
            None, load_model
        )
        
        self.is_loaded = True
        logger.info(f"LLM model {self.model_name} loaded successfully")
    
    async def generate_response(
        self, 
        prompt: str, 
        max_tokens: int = 256,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """Generate a response from the LLM."""
        if not self.is_loaded:
            await self.initialize()
        
        if stream:
            # For streaming, we'll collect all chunks and return the full response
            # In a real implementation, you'd yield chunks as they're generated
            full_response = ""
            async for chunk in self.generate_streaming_response(prompt, max_tokens, temperature):
                full_response += chunk
            return self.clean_response(full_response, prompt)
        else:
            return await self.generate_single_response(prompt, max_tokens, temperature)
    
    async def generate_single_response(
        self, 
        prompt: str, 
        max_tokens: int = 256,
        temperature: float = 0.7
    ) -> str:
        """Generate a single response without streaming."""
        loop = asyncio.get_event_loop()
        
        def generate():
            result = self.pipeline(
                prompt,
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=temperature,
                pad_token_id=self.tokenizer.eos_token_id,
                return_full_text=False
            )
            return result[0]["generated_text"]
        
        response = await loop.run_in_executor(None, generate)
        return self.clean_response(response, prompt)
    
    async def generate_streaming_response(
        self, 
        prompt: str, 
        max_tokens: int = 256,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response chunks."""
        # For DistilGPT-2, we'll simulate streaming by generating the full response
        # and yielding it in chunks. Real streaming would require a different approach.
        
        response = await self.generate_single_response(prompt, max_tokens, temperature)
        
        # Simulate streaming by yielding words
        words = response.split()
        for i, word in enumerate(words):
            if i == 0:
                yield word
            else:
                yield " " + word
            
            # Small delay to simulate real streaming
            await asyncio.sleep(0.05)
    
    def clean_response(self, response: str, original_prompt: str) -> str:
        """Clean up the generated response."""
        # Remove the original prompt if it's included
        if response.startswith(original_prompt):
            response = response[len(original_prompt):].strip()
        
        # Clean up excessive newlines
        response = re.sub(r'\n{2,}', '\n', response).strip()
        
        # Remove incomplete sentences at the end
        sentences = response.split('.')
        if len(sentences) > 1 and sentences[-1].strip() and not sentences[-1].strip().endswith(('!', '?')):
            # Last sentence might be incomplete, remove it
            response = '.'.join(sentences[:-1]) + '.'
        
        return response.strip()
    
    async def generate_with_context(
        self, 
        messages: list, 
        max_tokens: int = 256,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """Generate response with conversation context."""
        # Convert messages to a single prompt
        prompt = self.format_conversation(messages)
        return await self.generate_response(prompt, max_tokens, temperature, stream)
    
    def format_conversation(self, messages: list) -> str:
        """Format conversation messages into a prompt."""
        formatted = ""
        for message in messages[-5:]:  # Keep last 5 messages for context
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "user":
                formatted += f"User: {content}\n"
            elif role == "assistant":
                formatted += f"Assistant: {content}\n"
        
        formatted += "Assistant: "
        return formatted
    
    async def generate_with_function_context(
        self, 
        user_message: str,
        function_results: list = None,
        max_tokens: int = 256,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """Generate response considering function execution results."""
        prompt = f"User: {user_message}\n"
        
        if function_results:
            prompt += "\nFunction execution results:\n"
            for result in function_results:
                if result.get("isError", False):
                    prompt += f"- Error in {result.get('tool', 'unknown')}: {result.get('error', 'Unknown error')}\n"
                else:
                    prompt += f"- {result.get('tool', 'Function')} executed successfully\n"
        
        prompt += "\nAssistant: "
        
        return await self.generate_response(prompt, max_tokens, temperature, stream)

class MockLLMIntegration:
    """Mock LLM integration for testing without loading actual models."""
    
    def __init__(self):
        self.is_loaded = True
    
    async def initialize(self):
        """Mock initialization."""
        pass
    
    async def generate_response(
        self, 
        prompt: str, 
        max_tokens: int = 256,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """Generate a mock response."""
        return f"Mock response to: {prompt[:50]}..."
    
    async def generate_streaming_response(
        self, 
        prompt: str, 
        max_tokens: int = 256,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """Generate mock streaming response."""
        words = ["Mock", "streaming", "response", "to", "your", "request"]
        for word in words:
            yield word + " "
            await asyncio.sleep(0.1)
    
    async def generate_with_context(
        self, 
        messages: list, 
        max_tokens: int = 256,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """Generate mock response with context."""
        last_message = messages[-1].get("content", "") if messages else ""
        return f"Mock response to: {last_message[:50]}..."
    
    async def generate_with_function_context(
        self, 
        user_message: str,
        function_results: list = None,
        max_tokens: int = 256,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """Generate mock response with function context."""
        return f"Mock response to '{user_message}' with {len(function_results or [])} function results"
