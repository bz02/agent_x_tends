#!/usr/bin/env python3
"""
Voice Support Backend - Integrates analyze_and_support.py with voice calling
Uses Langraph for conversation management, Mem0 for memory, and LanceDB for RAG
"""

import os
import sys
import json
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
try:
    from analyze_and_support import GrokClient, TwitterClient
except ImportError:
    # If analyze_and_support is not available, create minimal stubs
    print("Warning: analyze_and_support.py not found. Some features may not work.")
    class GrokClient:
        def __init__(self, api_key): pass
    class TwitterClient:
        def __init__(self, bearer_token): pass

# Import memory and RAG components
from memory_manager import MemoryManager
from rag_manager import RAGManager
from conversation_graph import ConversationGraph

load_dotenv()

app = FastAPI(
    title="Voice Support Backend",
    description="Backend for voice support calls with conversation management",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
grok_client = GrokClient(os.getenv("GROK_API_KEY", ""))
twitter_client = TwitterClient(os.getenv("X_API_BEARER_TOKEN", ""))
memory_manager = MemoryManager()
rag_manager = RAGManager()
conversation_graph = ConversationGraph(grok_client, memory_manager, rag_manager)

# Store active conversations
active_conversations: Dict[str, Dict[str, Any]] = {}


class CallRequest(BaseModel):
    """Request to initiate a call"""
    user_id: str
    username: str
    phone_number: str
    context: Optional[Dict[str, Any]] = None


class ConversationMessage(BaseModel):
    """Message in a conversation"""
    role: str
    content: str
    timestamp: str


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Voice Support Backend",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "users_needing_support": "/api/users/needing-support",
            "initiate_call": "/api/calls/initiate",
            "conversation": "/api/conversations/{user_id}",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "memory": memory_manager.is_ready(),
        "rag": rag_manager.is_ready()
    }


@app.get("/api/users/needing-support")
async def get_users_needing_support():
    """
    Get list of users who need support from analyze_and_support.py results
    """
    # Look for the most recent support outreach JSON file
    support_files = sorted(
        Path(".").glob("support_outreach_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if not support_files:
        return {"users": []}
    
    try:
        with open(support_files[0], 'r') as f:
            data = json.load(f)
            return {
                "users": data.get("results", []),
                "scan_timestamp": data.get("scan_timestamp"),
                "total_found": len(data.get("results", []))
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/calls/initiate")
async def initiate_call(request: CallRequest):
    """
    Initiate a voice call to a user
    """
    try:
        # Get user's conversation history and context
        user_memory = memory_manager.get_user_memory(request.user_id)
        rag_context = rag_manager.get_relevant_context(
            user_id=request.user_id,
            query=request.context.get("original_post", "") if request.context else ""
        )
        
        # Create conversation entry
        conversation_id = f"conv_{request.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        active_conversations[conversation_id] = {
            "user_id": request.user_id,
            "username": request.username,
            "phone_number": request.phone_number,
            "context": request.context or {},
            "memory": user_memory,
            "rag_context": rag_context,
            "started_at": datetime.now().isoformat(),
            "messages": []
        }
        
        # Generate initial greeting using Langraph
        initial_message = await conversation_graph.generate_initial_greeting(
            user_id=request.user_id,
            username=request.username,
            context=request.context,
            memory=user_memory,
            rag_context=rag_context
        )
        
        return {
            "conversation_id": conversation_id,
            "initial_message": initial_message,
            "phone_number": request.phone_number,
            "status": "ready"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations/{user_id}")
async def get_conversation(user_id: str):
    """Get conversation history for a user"""
    user_memory = memory_manager.get_user_memory(user_id)
    conversations = memory_manager.get_conversation_history(user_id)
    
    return {
        "user_id": user_id,
        "memory": user_memory,
        "conversations": conversations,
        "total_messages": sum(len(conv.get("messages", [])) for conv in conversations)
    }


@app.post("/api/conversations/{conversation_id}/message")
async def add_message(conversation_id: str, message: ConversationMessage):
    """Add a message to a conversation"""
    if conversation_id not in active_conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conv = active_conversations[conversation_id]
    conv["messages"].append({
        "role": message.role,
        "content": message.content,
        "timestamp": message.timestamp
    })
    
    # Update memory
    memory_manager.add_message(
        user_id=conv["user_id"],
        role=message.role,
        content=message.content
    )
    
    return {"status": "added"}


@app.post("/api/conversations/{conversation_id}/generate-response")
async def generate_response(conversation_id: str, user_message: str):
    """Generate a response using Langraph"""
    if conversation_id not in active_conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conv = active_conversations[conversation_id]
    
    # Generate response using conversation graph
    response = await conversation_graph.generate_response(
        user_id=conv["user_id"],
        username=conv["username"],
        user_message=user_message,
        conversation_history=conv["messages"],
        memory=conv.get("memory", {}),
        rag_context=conv.get("rag_context", [])
    )
    
    return {
        "response": response["content"],
        "reasoning": response.get("reasoning", ""),
        "updated_memory": response.get("updated_memory", {})
    }


@app.websocket("/ws/conversation/{conversation_id}")
async def websocket_conversation(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time conversation"""
    await websocket.accept()
    
    if conversation_id not in active_conversations:
        await websocket.close(code=1008, reason="Conversation not found")
        return
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "user_message":
                # Generate response
                response = await generate_response(
                    conversation_id,
                    message_data.get("content", "")
                )
                
                # Send response
                await websocket.send_json({
                    "type": "assistant_message",
                    "content": response["response"],
                    "timestamp": datetime.now().isoformat()
                })
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for conversation {conversation_id}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8001")),
        log_level="info",
        reload=True
    )

