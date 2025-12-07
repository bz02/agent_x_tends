# Voice Support Backend

Backend service that integrates `analyze_and_support.py` with voice calling capabilities, using Langraph for conversation management, Mem0 for long-term memory, and LanceDB for RAG.

## Features

- **Conversation Management**: Uses Langraph to manage conversation flow
- **Long-term Memory**: Stores conversation history using Mem0 (with file-based fallback)
- **RAG**: Retrieves relevant support resources using LanceDB
- **Voice Integration**: Connects with TypeScript telephony service for voice calls
- **User Context**: Maintains context about users from sentiment analysis

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r ../requirements.txt
   ```

2. **Environment Variables**
   Create a `.env` file:
   ```
   GROK_API_KEY=your_grok_api_key
   X_API_BEARER_TOKEN=your_twitter_bearer_token
   PORT=8001
   ```

3. **Optional: Mem0 Setup**
   - Install Mem0: `pip install mem0ai`
   - Mem0 will use ChromaDB by default (file-based storage)
   - If not available, falls back to file-based storage

4. **Optional: LanceDB Setup**
   - Install LanceDB: `pip install lancedb`
   - If not available, uses fallback keyword matching

5. **Run the Server**
   ```bash
   python voice_support_backend/main.py
   ```

## API Endpoints

### GET `/`
Root endpoint with service information

### GET `/health`
Health check endpoint

### GET `/api/users/needing-support`
Get list of users who need support from `analyze_and_support.py` results

### POST `/api/calls/initiate`
Initiate a voice call to a user
```json
{
  "user_id": "user123",
  "username": "johndoe",
  "phone_number": "+1234567890",
  "context": {
    "original_post": "Feeling down today...",
    "sentiment_analysis": {...}
  }
}
```

### GET `/api/conversations/{user_id}`
Get conversation history for a user

### POST `/api/conversations/{conversation_id}/message`
Add a message to a conversation

### POST `/api/conversations/{conversation_id}/generate-response`
Generate a response using Langraph

### WebSocket `/ws/conversation/{conversation_id}`
Real-time conversation WebSocket endpoint

## Architecture

- **main.py**: FastAPI server with endpoints
- **memory_manager.py**: Manages long-term memory (Mem0 or file-based)
- **rag_manager.py**: Manages RAG with LanceDB (or fallback)
- **conversation_graph.py**: Langraph-based conversation management

## Integration with Telephony

The backend provides conversation context to the TypeScript telephony service:
1. Telephony service calls `/api/calls/initiate` to prepare conversation
2. Backend generates initial greeting using Langraph
3. During call, transcripts are sent to backend for memory storage
4. Backend provides context-aware responses

## Memory Storage

Conversations are stored in `./conversation_storage/` directory:
- `{user_id}_memory.json`: User memories
- `{user_id}_history.json`: Conversation history

## RAG Storage

Support resources are stored in `./lancedb_storage/` directory (if LanceDB is available).

