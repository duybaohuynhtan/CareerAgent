"""
FastAPI Server for Resume Analyzer Chat Interface
Serves as a bridge between the Next.js frontend and the conversation agent.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
import traceback
from datetime import datetime
import json

# Import the job search agent
from job_search_agent import create_linkedin_job_agent
from config import MODEL_NAME, update_model_name, get_current_model, get_available_models

app = FastAPI(
    title="Resume Analyzer API",
    description="FastAPI backend for Resume Analyzer conversation agent",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Alternative port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class ChatMessage(BaseModel):
    id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    chatHistory: List[ChatMessage] = Field(default=[], description="Previous chat messages")

class UpdateModelRequest(BaseModel):
    model: str = Field(..., description="Model name to switch to")

class UpdateModelResponse(BaseModel):
    success: bool = Field(..., description="Whether the update was successful")
    message: str = Field(..., description="Response message")
    current_model: str = Field(..., description="Current active model")

class GetModelResponse(BaseModel):
    current_model: str = Field(..., description="Current active model")
    available_models: List[str] = Field(..., description="List of available models")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Agent response")
    success: bool = Field(..., description="Whether the request was successful")
    error: Optional[str] = Field(None, description="Error message if any")

# Global agents cache to avoid recreating agents
agents_cache = {}

def get_agent():
    """Get or create an agent"""
    if MODEL_NAME not in agents_cache:
        try:
            agents_cache[MODEL_NAME] = create_linkedin_job_agent()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")
    
    return agents_cache[MODEL_NAME]

def format_chat_history_for_agent(chat_history: List[ChatMessage]) -> str:
    """Convert chat history to string format for the agent"""
    if not chat_history:
        return ""
    
    formatted_history = []
    for msg in chat_history:
        role = "Human" if msg.role == "user" else "Assistant"
        formatted_history.append(f"{role}: {msg.content}")
    
    return "\n".join(formatted_history)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/api/model", response_model=GetModelResponse)
async def get_current_model_info():
    """Get current model and available models"""
    return GetModelResponse(
        current_model=get_current_model(),
        available_models=get_available_models()
    )

@app.post("/api/model", response_model=UpdateModelResponse)
async def update_model(request: UpdateModelRequest):
    """Update the global model configuration"""
    try:
        success = update_model_name(request.model)
        
        if success:
            # Clear agents cache to force recreation with new model
            global agents_cache
            agents_cache.clear()
            
            return UpdateModelResponse(
                success=True,
                message=f"Model updated to {request.model}",
                current_model=get_current_model()
            )
        else:
            available = get_available_models()
            return UpdateModelResponse(
                success=False,
                message=f"Invalid model '{request.model}'. Available models: {', '.join(available)}",
                current_model=get_current_model()
            )
    except Exception as e:
        return UpdateModelResponse(
            success=False,
            message=f"Error updating model: {str(e)}",
            current_model=get_current_model()
        )

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint that processes user messages through the conversation agent"""
    
    try:
        # Model is now handled globally, no need to validate per request
        
        # Get the agent
        agent = get_agent()
        
        # Prepare the input for the agent
        # The agent expects the current user input
        user_input = request.message
        
        # Clear the agent's memory and set chat history if provided
        if request.chatHistory:
            # Reset memory
            agent.memory.clear()
            
            # Add chat history to memory
            for msg in request.chatHistory:
                if msg.role == "user":
                    agent.memory.save_context(
                        {"input": msg.content},
                        {"output": ""}  # Placeholder for user messages
                    )
                elif msg.role == "assistant":
                    # Update the last output in memory
                    if agent.memory.buffer:
                        # Get the last human input and update with this assistant response
                        agent.memory.buffer[-1].content = agent.memory.buffer[-1].content.replace(
                            "Assistant: ", f"Assistant: {msg.content}"
                        )
        
        # Run the agent with the user input
        response = agent.invoke({
            "input": user_input
        })
        
        # Extract the response
        agent_response = response.get("output", "Sorry, I couldn't process this request.")
        
        return ChatResponse(
            response=agent_response,
            success=True
        )
        
    except Exception as e:
        # Log the full error
        error_details = traceback.format_exc()
        print(f"Error in chat endpoint: {error_details}")
        
        return ChatResponse(
            response="Sorry, an error occurred during processing. Please try again.",
            success=False,
            error=str(e)
        )

@app.get("/api/models")
async def get_available_models():
    """Get list of available models"""
    models = [
        {
            "id": "deepseek-r1-distill-llama-70b",
            "name": "DeepSeek R1 Distill Llama 70B",
            "description": "Advanced reasoning model for complex tasks"
        },
        {
            "id": "llama-3.3-70b-versatile",
            "name": "Llama 3.3 70B Versatile", 
            "description": "Versatile model for general conversations"
        },
        {
            "id": "gemma2-9b-it",
            "name": "Gemma2 9B IT",
            "description": "Efficient model for instruction following"
        }
    ]
    return {"models": models}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Resume Analyzer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    print("🚀 Starting Resume Analyzer FastAPI Server...")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔗 Frontend should connect to: http://localhost:8000")
    
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )