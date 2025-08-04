"""
FastAPI Server for CareerAgent Chat Interface
Serves as a bridge between the Next.js frontend and the conversation agent.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
import traceback
from datetime import datetime, timedelta
import json
import os
import tempfile
import shutil
from pathlib import Path

# Import the job search agent
from job_search_agent import create_linkedin_job_agent
from config import update_model_name, get_current_model, get_available_models, get_available_models_detailed

app = FastAPI(
    title="CareerAgent API",
    description="FastAPI backend for CareerAgent conversation agent",
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

class ClearChatResponse(BaseModel):
    success: bool = Field(..., description="Whether the clear operation was successful")
    message: str = Field(..., description="Response message")

class UploadResponse(BaseModel):
    success: bool = Field(..., description="Whether the upload was successful")
    message: str = Field(..., description="Response message")
    file_id: Optional[str] = Field(None, description="Unique file identifier")
    cv_analysis: Optional[str] = Field(None, description="AI analysis of the uploaded CV")

# Global agents cache to avoid recreating agents
agents_cache = {}

# File management system
uploaded_files = {}  # {file_id: {"path": str, "original_name": str, "upload_time": datetime}}
UPLOAD_DIR = Path(tempfile.gettempdir()) / "career_agent_uploads"

# Ensure upload directory exists
UPLOAD_DIR.mkdir(exist_ok=True)

def get_agent():
    """Get or create an agent"""
    AGENT_KEY = "current_agent"  # Use fixed key instead of MODEL_NAME
    
    if AGENT_KEY not in agents_cache:
        try:
            agents_cache[AGENT_KEY] = create_linkedin_job_agent()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")
    
    return agents_cache[AGENT_KEY]

def generate_file_id() -> str:
    """Generate unique file ID"""
    import uuid
    return str(uuid.uuid4())

def save_uploaded_file(file: UploadFile) -> tuple[str, str]:
    """Save uploaded file and return file_id and file_path"""
    file_id = generate_file_id()
    file_extension = Path(file.filename).suffix.lower() if file.filename else ""
    file_path = UPLOAD_DIR / f"{file_id}{file_extension}"
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Store file info
    uploaded_files[file_id] = {
        "path": str(file_path),
        "original_name": file.filename or "unknown",
        "upload_time": datetime.now()
    }
    
    return file_id, str(file_path)

def cleanup_user_files():
    """Clean up all uploaded files"""
    for file_id, file_info in uploaded_files.copy().items():
        try:
            if os.path.exists(file_info["path"]):
                os.remove(file_info["path"])
        except Exception as e:
            print(f"Error deleting file {file_info['path']}: {e}")
        finally:
            uploaded_files.pop(file_id, None)

def cleanup_old_files(max_age_hours: int = 24):
    """Clean up files older than specified hours"""
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    for file_id, file_info in uploaded_files.copy().items():
        if file_info["upload_time"] < cutoff_time:
            try:
                if os.path.exists(file_info["path"]):
                    os.remove(file_info["path"])
            except Exception as e:
                print(f"Error deleting old file {file_info['path']}: {e}")
            finally:
                uploaded_files.pop(file_id, None)

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

@app.get("/api/debug/agent-model")
async def debug_agent_model():
    """Debug endpoint to check what model the agent is actually using"""
    try:
        agent = get_agent()
        # Try to get the model name from the agent's model
        current_config_model = get_current_model()
        
        # Try to extract model from agent (this might vary depending on LangChain version)
        agent_model_info = "Unknown"
        try:
            if hasattr(agent, 'agent') and hasattr(agent.agent, 'runnable'):
                # Navigate through the chain to find the model
                runnable = agent.agent.runnable
                if hasattr(runnable, 'steps') and len(runnable.steps) > 1:
                    model_step = runnable.steps[1]  # Usually the model is the 2nd step
                    if hasattr(model_step, 'model'):
                        agent_model_info = model_step.model
                    elif hasattr(model_step, 'model_name'):
                        agent_model_info = model_step.model_name
        except Exception as e:
            agent_model_info = f"Error extracting model info: {str(e)}"
        
        return {
            "config_model": current_config_model,
            "agent_model_info": agent_model_info,
            "agent_cache_size": len(agents_cache),
            "agent_exists": "current_agent" in agents_cache
        }
    except Exception as e:
        return {
            "error": str(e),
            "config_model": get_current_model(),
            "agent_cache_size": len(agents_cache)
        }

@app.get("/api/model", response_model=GetModelResponse)
async def get_current_model_info():
    """Get current model and available models"""
    return GetModelResponse(
        current_model=get_current_model(),
        available_models=get_available_models()
    )

@app.post("/api/model", response_model=UpdateModelResponse)
async def update_model(request: UpdateModelRequest):
    """Update the global model configuration and reset agent"""
    try:
        success = update_model_name(request.model)
        
        if success:
            # Clear agents cache to force recreation with new model
            global agents_cache
            print(f"Clearing agent cache. Previous cache size: {len(agents_cache)}")
            agents_cache.clear()
            print(f"Agent cache cleared. New cache size: {len(agents_cache)}")
            
            # Clean up uploaded files since we're resetting
            cleanup_user_files()
            
            return UpdateModelResponse(
                success=True,
                message=f"Model updated to {request.model}. Chat history and files have been cleared.",
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
        
        # Handle chat history - if no history provided, treat as fresh start
        if not request.chatHistory:
            # No history means fresh start - clear agent memory
            agent.memory.clear()
        else:
            # Reset memory and restore provided history
            agent.memory.clear()
            
            # Add chat history to memory properly
            i = 0
            while i < len(request.chatHistory):
                msg = request.chatHistory[i]
                if msg.role == "user":
                    # Look for corresponding assistant response
                    assistant_response = ""
                    if i + 1 < len(request.chatHistory) and request.chatHistory[i + 1].role == "assistant":
                        assistant_response = request.chatHistory[i + 1].content
                        i += 1  # Skip the assistant message in next iteration
                    
                    # Save the conversation pair
                    agent.memory.save_context(
                        {"input": msg.content},
                        {"output": assistant_response}
                    )
                i += 1
        
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

@app.post("/api/chat/clear", response_model=ClearChatResponse)
async def clear_chat():
    """Clear chat history, reset agent, and cleanup uploaded files"""
    try:
        # Get current agent and clear its memory
        agent = get_agent()
        agent.memory.clear()
        
        # Clean up uploaded files
        cleanup_user_files()
        
        return ClearChatResponse(
            success=True,
            message="Chat history and uploaded files cleared successfully"
        )
    except Exception as e:
        return ClearChatResponse(
            success=False,
            message=f"Error clearing chat: {str(e)}"
        )

@app.post("/api/upload/cv", response_model=UploadResponse)
async def upload_cv(file: UploadFile = File(...)):
    """Upload CV/Resume file and automatically analyze it"""
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ['.pdf', '.doc', '.docx', '.txt']:
            raise HTTPException(
                status_code=400, 
                detail="Only PDF, DOC, DOCX, and TXT files are supported"
            )
        
        # Clean up old files before saving new one
        cleanup_old_files(max_age_hours=1)  # Clean files older than 1 hour
        
        # Save file
        file_id, file_path = save_uploaded_file(file)
        
        # Get agent and analyze CV
        agent = get_agent()
        
        # Use the CV parser tool to analyze the uploaded file
        try:
            if file_extension == '.pdf':
                cv_analysis_result = agent.invoke({
                    "input": f"I've uploaded a PDF CV file. Please analyze it. File path: {file_path}"
                })
            else:
                # For other file types, read content directly
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                cv_analysis_result = agent.invoke({
                    "input": f"Please analyze this CV content: {file_content[:2000]}..."  # Limit content size
                })
            
            cv_analysis = cv_analysis_result.get("output", "CV analysis completed")
            
        except Exception as e:
            print(f"Error analyzing CV: {e}")
            cv_analysis = f"CV uploaded successfully as '{file.filename}'. You can ask me to analyze it or search for jobs based on your profile."
        
        return UploadResponse(
            success=True,
            message=f"CV '{file.filename}' uploaded and analyzed successfully",
            file_id=file_id,
            cv_analysis=cv_analysis
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return UploadResponse(
            success=False,
            message=f"Error uploading file: {str(e)}"
        )

@app.get("/api/models")
async def get_models_endpoint():
    """Get list of available models from centralized configuration"""
    try:
        models = get_available_models_detailed()
        return {"models": models}
    except Exception as e:
        # Fallback to basic model list if detailed fetch fails
        basic_models = [
            {
                "id": model_id,
                "name": model_id.replace("-", " ").title(),
                "description": "AI model for conversation and task completion",
                "provider": "groq"
            }
            for model_id in get_available_models()
        ]
        return {"models": basic_models}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "CareerAgent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    print("🚀 Starting CareerAgent FastAPI Server...")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔗 Frontend should connect to: http://localhost:8000")
    
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )