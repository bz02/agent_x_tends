# Voice Support System - Complete Setup Guide

This guide will help you set up the complete voice support system that integrates `analyze_and_support.py` with voice calling, conversation management, and a Unity UI.

## System Architecture

```
┌─────────────────┐
│  Unity UI       │  ← User Interface
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Python Backend  │  ← Langraph, Mem0, LanceDB
│ (FastAPI)       │
└────────┬────────┘
         │
         ├─────────► analyze_and_support.py (gets users needing support)
         │
         ▼
┌─────────────────┐
│ TypeScript      │  ← Voice calling with xAI Grok
│ Telephony       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Twilio         │  ← Phone calls
│  xAI Grok API   │  ← Voice AI
└─────────────────┘
```

## Prerequisites

1. **Python 3.9+**
2. **Node.js 18+**
3. **Unity 2021.3+** (for UI)
4. **Twilio Account** with phone number
5. **xAI API Key** (Grok)
6. **X (Twitter) API Bearer Token**

## Step 1: Python Backend Setup

### 1.1 Install Dependencies

```bash
cd /path/to/agent_x_tends
pip install -r requirements.txt
```

### 1.2 Environment Variables

Create a `.env` file in the project root:

```bash
# Grok API
GROK_API_KEY=your_grok_api_key_here

# Twitter API
X_API_BEARER_TOKEN=your_twitter_bearer_token_here

# Backend Port
PORT=8001
```

### 1.3 Optional: Install Memory & RAG Libraries

For full functionality, install optional dependencies:

```bash
# Mem0 for long-term memory
pip install mem0ai chromadb

# LanceDB for RAG
pip install lancedb
```

Note: The system will work with file-based fallbacks if these are not installed.

### 1.4 Run Backend

```bash
cd voice_support_backend
python main.py
```

The backend will start on `http://localhost:8001`

## Step 2: TypeScript Telephony Setup

### 2.1 Install Dependencies

```bash
cd xai-voice-examples-main/examples/agent/telephony/xai
npm install
```

### 2.2 Environment Variables

Create a `.env` file:

```bash
XAI_API_KEY=your_grok_api_key_here
HOSTNAME=https://your-ngrok-domain.ngrok.app
BACKEND_URL=http://localhost:8001
PORT=3000
```

### 2.3 Setup ngrok

```bash
ngrok http 3000
```

Copy the ngrok domain and update `HOSTNAME` in `.env`.

### 2.4 Configure Twilio

1. Go to [Twilio Console](https://console.twilio.com/)
2. Configure your phone number webhooks:
   - **Incoming Call Webhook**: `https://your-ngrok-domain.ngrok.app/twiml`
   - **Call Status Update Webhook**: `https://your-ngrok-domain.ngrok.app/call-status`

### 2.5 Run Telephony Server

```bash
npm run dev
```

## Step 3: Unity UI Setup

### 3.1 Open Unity Project

1. Open Unity Hub
2. Create new project or open existing
3. Import the `UnityUI/Assets` folder into your project

### 3.2 Install TextMeshPro

1. Window > TextMeshPro > Import TMP Essential Resources
2. Import if prompted

### 3.3 Create UI Scene

1. Create a new scene
2. Add Canvas (UI > Canvas)
3. Create UI elements:

**User List Panel:**
- ScrollView (for user list)
- Content GameObject inside ScrollView

**Control Panel:**
- Button: "Refresh Users"
- Button: "Initiate Call"
- InputField: "Phone Number"
- Text: "Status"

**Conversation Panel:**
- ScrollView (for conversation)
- Text (for conversation display)

### 3.4 Setup Scripts

1. Create empty GameObject named "SupportCallManager"
2. Add `SupportCallManager` component
3. Assign UI references:
   - User List Container: Content GameObject from ScrollView
   - User Item Prefab: Create prefab with UserListItem component
   - Status Text: Status Text element
   - Refresh Button: Refresh button
   - Call Button: Call button
   - Phone Number Input: Phone number InputField
   - Conversation Text: Conversation Text element
   - Conversation Scroll Rect: Conversation ScrollView

### 3.5 Configure API URLs

In SupportCallManager component:
- Backend URL: `http://localhost:8001`
- Telephony URL: `http://localhost:3000`

### 3.6 Create User Item Prefab

1. Create UI > Panel
2. Add UserListItem component
3. Add child Text elements:
   - Username Text
   - Post Text
   - Sentiment Text
4. Add Button component
5. Save as Prefab

## Step 4: Running the System

### 4.1 Start Services

1. **Python Backend**:
   ```bash
   cd voice_support_backend
   python main.py
   ```

2. **TypeScript Telephony**:
   ```bash
   cd xai-voice-examples-main/examples/agent/telephony/xai
   npm run dev
   ```

3. **Unity UI**: Run in Unity Editor

### 4.2 Generate User List

First, run `analyze_and_support.py` to generate a list of users needing support:

```bash
python analyze_and_support.py --query "feeling sad" --max-posts 20
```

This creates a `support_outreach_*.json` file that the backend reads.

### 4.3 Use the System

1. In Unity UI, click "Refresh Users"
2. Select a user from the list
3. Enter phone number
4. Click "Initiate Call"
5. The system will:
   - Prepare conversation context
   - Generate personalized greeting
   - Initiate Twilio call (you'll need to implement Twilio call initiation)
   - Store conversation in memory
   - Use RAG for support resources

## API Endpoints Reference

### Backend API (Port 8001)

- `GET /api/users/needing-support` - Get users needing support
- `POST /api/calls/initiate` - Initiate a call
- `GET /api/conversations/{user_id}` - Get conversation history
- `POST /api/conversations/{conversation_id}/message` - Add message
- `POST /api/conversations/{conversation_id}/generate-response` - Generate response
- `WebSocket /ws/conversation/{conversation_id}` - Real-time conversation

### Telephony API (Port 3000)

- `POST /twiml` - Twilio webhook for incoming calls
- `POST /call-status` - Twilio call status updates
- `POST /api/calls/initiate` - Initiate call from backend
- `WebSocket /media-stream/{callId}` - Media stream endpoint

## Troubleshooting

### Backend Issues

- **Mem0 not working**: System falls back to file-based storage automatically
- **LanceDB not working**: System uses keyword matching fallback
- **Import errors**: Make sure all dependencies are installed

### Telephony Issues

- **WebSocket errors**: Check ngrok is running and HOSTNAME is correct
- **No audio**: Verify xAI API key and WebSocket connection
- **Call not connecting**: Check Twilio webhook configuration

### Unity Issues

- **JSON parsing errors**: Check API responses are valid JSON
- **No users showing**: Run `analyze_and_support.py` first to generate user list
- **Connection errors**: Verify backend and telephony services are running

## Next Steps

1. **Implement Twilio Call Initiation**: Add code to actually place calls via Twilio API
2. **Add Real-time Updates**: Use WebSocket in Unity for live conversation updates
3. **Enhance UI**: Add more features like call history, user profiles, etc.
4. **Deploy**: Deploy backend and telephony services to production servers

## File Structure

```
agent_x_tends/
├── analyze_and_support.py          # Original script
├── voice_support_backend/           # Python backend
│   ├── main.py                      # FastAPI server
│   ├── memory_manager.py            # Mem0 integration
│   ├── rag_manager.py               # LanceDB integration
│   └── conversation_graph.py        # Langraph integration
├── xai-voice-examples-main/         # Voice examples
│   └── examples/agent/telephony/xai/ # Telephony service
│       └── src/
│           ├── index.ts             # Main server (modified)
│           └── bot.ts               # Bot config (modified)
└── UnityUI/                          # Unity project
    └── Assets/Scripts/
        ├── SupportCallManager.cs     # Main manager
        └── UserListItem.cs           # User list item
```

## Support

For issues or questions:
1. Check the README files in each component
2. Review API documentation
3. Check logs for error messages

