from fastapi import FastAPI, Request
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import uvicorn
import logging
from dummy_app import MockApp
from function_calling import FunctionCallingSystem

# Pydantic models for MCP
class Message(BaseModel):
    role: str
    content: str

class AskRequest(BaseModel):
    messages: list[Message]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

# Initialize FastAPI, LLM, and mock application
app = FastAPI()
mock_app = MockApp()

# Initialize function calling system
function_system = FunctionCallingSystem()

# Register mock app functions
function_system.register_function(
    "create_user", 
    mock_app.create_user,
    {"user_id": "string", "name": "string"}
)
function_system.register_function(
    "get_user", 
    mock_app.get_user,
    {"user_id": "string"}
)

# Load demo model (public, open-access)
MODEL_NAME = "distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
llama_pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)

@app.post("/ask")
async def ask(request: AskRequest):
    # Get the last user message
    user_message = request.messages[-1].content
    logger.info(f"Processing message: {user_message}")
    
    # Process function calls first
    function_results = function_system.process_message(user_message)
    
    # Generate LLM response
    generation = llama_pipe(user_message, max_new_tokens=256, do_sample=True, temperature=0.1)
    response_text = generation[0]["generated_text"]
    
    # Clean up excessive newlines in the response
    import re
    cleaned_text = re.sub(r'\n{2,}', '\n', response_text).strip()
    
    # Prepare the response
    response_content = cleaned_text
    
    # If functions were executed, add their results to the response
    if function_results:
        function_summary = "\n\n--- Function Execution Results ---\n"
        for result in function_results:
            if result.success:
                function_summary += f"✅ {result.function_name}({', '.join(f'{k}={v}' for k, v in result.parameters.items())})\n"
                function_summary += f"   Result: {result.result}\n"
            else:
                function_summary += f"❌ {result.function_name}({', '.join(f'{k}={v}' for k, v in result.parameters.items())})\n"
                function_summary += f"   Error: {result.error}\n"
        
        response_content += function_summary
    
    # Return enhanced MCP-compatible response
    return {
        "choices": [{"message": {"role": "assistant", "content": response_content}}],
        "function_calls": [
            {
                "function": result.function_name,
                "parameters": result.parameters,
                "result": result.result,
                "success": result.success,
                "error": result.error
            } for result in function_results
        ] if function_results else []
    }

@app.post("/tools/create_user")
async def create_user_tool(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    name = data.get("name")
    result = mock_app.create_user(user_id, name)
    return result

@app.post("/tools/get_user")
async def get_user_tool(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    result = mock_app.get_user(user_id)
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
