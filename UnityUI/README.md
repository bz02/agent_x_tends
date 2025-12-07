# Unity UI for Voice Support System

This Unity project provides a user interface for managing voice support calls to users who need emotional support.

## Features

- View users who need support (from analyze_and_support.py results)
- See sentiment analysis and concerns for each user
- Initiate voice calls to users
- View conversation history
- Real-time conversation updates

## Setup

1. **Import into Unity**
   - Open Unity Hub
   - Create a new project or open existing
   - Import the Assets folder into your Unity project

2. **Install TextMeshPro** (if not already installed)
   - Window > TextMeshPro > Import TMP Essential Resources

3. **Configure API URLs**
   - Select the SupportCallManager GameObject
   - Set `backendUrl` to your Python backend (default: http://localhost:8001)
   - Set `telephonyUrl` to your TypeScript telephony server (default: http://localhost:3000)

4. **Create UI**
   - Create a Canvas
   - Add UI elements:
     - ScrollView for user list
     - Text for status display
     - Button for refresh
     - Button for initiate call
     - InputField for phone number
     - ScrollView for conversation display

5. **Assign References**
   - Drag UI elements to SupportCallManager component
   - Create UserListItem prefab with username, post, and sentiment text

## Usage

1. Start the backend services:
   - Python backend: `python voice_support_backend/main.py`
   - TypeScript telephony: `npm run dev` in telephony/xai directory

2. Run Unity project

3. Click "Refresh" to load users needing support

4. Select a user from the list

5. Enter phone number and click "Initiate Call"

6. View conversation history as it updates

## UI Components

- **User List**: Shows all users who need support with their posts and sentiment
- **Status Text**: Displays current operation status
- **Phone Number Input**: Enter phone number for calling
- **Conversation Display**: Shows conversation history with user
- **Call Button**: Initiates a voice call to selected user

## API Integration

The Unity UI communicates with:
- Backend API (`/api/users/needing-support`, `/api/conversations/{user_id}`, `/api/calls/initiate`)
- Telephony API (`/api/calls/initiate`)

Make sure both services are running before using the Unity UI.

