# Voice Support System Integration

This document describes the complete integration of `analyze_and_support.py` with voice calling, conversation management, and Unity UI.

## Overview

The system provides a complete solution for:
1. **Identifying users needing support** via `analyze_and_support.py`
2. **Making voice calls** to provide emotional support
3. **Managing conversations** with Langraph
4. **Storing memories** with Mem0
5. **Retrieving support resources** with LanceDB RAG
6. **Visualizing and managing** with Unity UI

## Components

### 1. Python Backend (`voice_support_backend/`)

**Main Features:**
- FastAPI server for API endpoints
- Langraph for conversation flow management
- Mem0 for long-term memory storage
- LanceDB for RAG (Retrieval-Augmented Generation)
- Integration with `analyze_and_support.py`

**Key Files:**
- `main.py`: FastAPI server with REST and WebSocket endpoints
- `memory_manager.py`: Manages user memories (Mem0 or file-based fallback)
- `rag_manager.py`: Manages support resources and context retrieval
- `conversation_graph.py`: Langraph-based conversation management
- `initiate_call.py`: Helper script for Twilio call initiation

### 2. TypeScript Telephony Service (`xai-voice-examples-main/examples/agent/telephony/xai/`)

**Main Features:**
- Twilio integration for voice calls
- xAI Grok Realtime API for voice AI
- WebSocket media streaming
- Integration with Python backend for context

**Key Modifications:**
- `src/index.ts`: Added backend integration, conversation context loading
- `src/bot.ts`: Added dynamic instruction generation based on user context

### 3. Unity UI (`UnityUI/`)

**Main Features:**
- View users needing support
- Initiate voice calls
- View conversation history
- Real-time status updates

**Key Scripts:**
- `SupportCallManager.cs`: Main manager for UI and API communication
- `UserListItem.cs`: Component for displaying users in list

## Data Flow

```
1. analyze_and_support.py
   ↓ (generates support_outreach_*.json)
   
2. Python Backend
   ↓ (reads JSON, prepares context)
   
3. Unity UI
   ↓ (user selects user, initiates call)
   
4. TypeScript Telephony
   ↓ (receives call request, loads context)
   
5. Twilio + xAI Grok
   ↓ (makes call, processes audio)
   
6. Python Backend
   ↓ (stores conversation, updates memory)
   
7. Unity UI
   ↓ (displays conversation history)
```

## Conversation Management Flow

### Using Langraph

The conversation graph has the following nodes:

1. **analyze_context**: Analyzes user message and context
2. **retrieve_memory**: Searches for relevant past conversations
3. **generate_response**: Generates response using Grok with RAG context
4. **update_memory**: Stores new information in memory

### Memory Storage

- **Mem0**: Stores user memories as vectors for semantic search
- **Fallback**: File-based storage in `./conversation_storage/`
- **Format**: JSON files with user_id as key

### RAG System

- **LanceDB**: Vector database for support resources
- **Fallback**: Keyword-based matching
- **Resources**: Pre-loaded support messages for different situations

## API Integration

### Backend → Telephony

1. Backend receives call initiation request
2. Loads user context from `analyze_and_support.py` results
3. Retrieves conversation history from memory
4. Gets relevant support resources from RAG
5. Generates initial greeting using Langraph
6. Returns conversation_id and context to telephony service

### Telephony → Backend

1. Telephony service receives call
2. Fetches user context from backend (if user_id provided)
3. Uses context to personalize bot instructions
4. During call, sends transcripts to backend
5. Backend stores in memory and updates conversation

### Unity → Backend/Telephony

1. Unity loads users from backend
2. User selects a user and enters phone number
3. Unity sends call request to telephony service
4. Telephony service initiates call via Twilio
5. Unity polls backend for conversation updates

## Context Engineering

The system uses multiple sources of context:

1. **Original Post**: From `analyze_and_support.py` sentiment analysis
2. **Sentiment Analysis**: Concerns, severity, reasoning
3. **Conversation History**: Past interactions with user
4. **Memory**: Important facts about user
5. **RAG Context**: Relevant support resources

All context is combined in the Langraph conversation graph to generate personalized, context-aware responses.

## Long-term Memory (Mem0)

### Features

- **Semantic Search**: Find relevant past conversations
- **User-specific**: Memories are scoped to user_id
- **Metadata**: Stores timestamps, context, etc.
- **Automatic Extraction**: Important information extracted from conversations

### Storage

- **Production**: Mem0 with ChromaDB vector store
- **Development**: File-based JSON storage
- **Location**: `./conversation_storage/` or `./mem0_storage/`

## RAG (LanceDB)

### Support Resources

Pre-loaded resources include:
- Emotional support messages
- Coping strategies
- Encouragement messages
- Self-compassion guidance
- Professional help resources

### Retrieval

- **Query**: User's current message or concern
- **Method**: Vector similarity search
- **Results**: Top 3 most relevant resources
- **Usage**: Included in Grok prompt for context-aware responses

## Usage Example

### 1. Generate User List

```bash
python analyze_and_support.py --query "feeling sad" --max-posts 20
```

This creates `support_outreach_YYYYMMDD_HHMMSS.json`

### 2. Start Services

```bash
# Terminal 1: Python Backend
cd voice_support_backend
python main.py

# Terminal 2: TypeScript Telephony
cd xai-voice-examples-main/examples/agent/telephony/xai
npm run dev

# Terminal 3: ngrok
ngrok http 3000
```

### 3. Use Unity UI

1. Open Unity project
2. Click "Refresh Users"
3. Select a user
4. Enter phone number
5. Click "Initiate Call"

### 4. Call Flow

1. Backend prepares conversation context
2. Telephony service receives call request
3. Twilio initiates call
4. xAI Grok processes audio in real-time
5. Transcripts sent to backend for storage
6. Conversation history updated in Unity UI

## Environment Variables

### Python Backend

```bash
GROK_API_KEY=your_key
X_API_BEARER_TOKEN=your_token
PORT=8001
```

### TypeScript Telephony

```bash
XAI_API_KEY=your_key
HOSTNAME=https://your-ngrok-domain.ngrok.app
BACKEND_URL=http://localhost:8001
PORT=3000
```

### Twilio (for call initiation)

```bash
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WEBHOOK_URL=https://your-ngrok-domain.ngrok.app/twiml
```

## Troubleshooting

### Backend can't find analyze_and_support.py

- Make sure you're running from the project root
- Check that `analyze_and_support.py` is in the parent directory
- The backend adds the parent directory to sys.path automatically

### Memory not persisting

- Check `./conversation_storage/` directory exists
- Verify file permissions
- If using Mem0, check `./mem0_storage/` directory

### RAG not working

- LanceDB is optional - system uses fallback if not available
- Check that support resources are loaded (see `rag_manager.py`)
- Verify embeddings are generated correctly

### Unity can't connect

- Verify backend is running on port 8001
- Check CORS settings in backend
- Verify API URLs in Unity are correct

## Next Steps

1. **Production Deployment**: Deploy backend and telephony to servers
2. **Enhanced UI**: Add more features to Unity UI
3. **Analytics**: Track call success, user satisfaction
4. **Scaling**: Add load balancing, database for production
5. **Security**: Add authentication, rate limiting

## References

- [xAI Grok API Docs](https://docs.x.ai/docs/tutorial)
- [Langraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Mem0 Documentation](https://docs.mem0.ai/)
- [LanceDB Documentation](https://lancedb.github.io/lancedb/)
- [Twilio Voice API](https://www.twilio.com/docs/voice)

