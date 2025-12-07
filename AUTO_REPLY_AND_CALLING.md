# Auto-Reply and Automated Calling Feature

This document describes the automated reply and calling system that responds to negative posts and initiates voice calls when users agree to talk.

## Overview

The system now automatically:
1. **Detects negative posts** using sentiment analysis
2. **Replies to posts** offering AI therapist conversation
3. **Monitors user responses** to the offers
4. **Initiates voice calls** when users agree to talk
5. **Provides supportive conversations** to help users feel better

## Workflow

```
1. Scan posts → Analyze sentiment
   ↓
2. Detect negative posts needing support
   ↓
3. Generate and send reply offering AI therapist
   ↓
4. Monitor for user responses (yes, talk, etc.)
   ↓
5. Analyze response sentiment
   ↓
6. Initiate voice call if user agrees
   ↓
7. Have supportive conversation to help them feel better
```

## Usage

### Step 1: Scan and Reply to Negative Posts

Run the main script with auto-reply enabled (default):

```bash
python analyze_and_support.py --query "feeling sad" --max-posts 50
```

This will:
- Scan posts matching the query
- Analyze sentiment for each post
- Automatically reply to negative posts offering AI therapist
- Track all offers sent

**Options:**
- `--auto-reply` (default): Enable automatic replies
- `--no-auto-reply`: Disable automatic replies
- `--dry-run`: Test without actually sending replies

### Step 2: Monitor for User Responses

Start the monitoring service to watch for user responses:

```bash
python start_monitoring.py
```

This will:
- Check for user responses every 5 minutes
- Analyze if responses indicate they want to talk
- Automatically initiate calls when users agree
- Track all interactions

**Note:** The monitoring service needs to be configured to check mentions/replies via Twitter API. See "Implementation Notes" below.

## Response Tracking

All interactions are tracked in `./response_tracking/user_responses.json`:

```json
{
  "offers_sent": {
    "user123_tweet456": {
      "user_id": "user123",
      "username": "johndoe",
      "tweet_id": "tweet456",
      "reply_id": "reply789",
      "timestamp": "2024-01-01T12:00:00",
      "status": "pending"
    }
  },
  "user_responses": {},
  "calls_initiated": {}
}
```

## Reply Message Format

The system generates personalized replies like:

> "Hey @username, I saw your post and I'm here if you'd like to talk. Reply 'yes' if you'd like to chat with an AI therapist who can help. 💙"

The reply is:
- Personalized based on their post
- Empathetic and non-intrusive
- Clear about how to indicate interest
- Within Twitter's 280 character limit

## Response Detection

The system detects positive responses using:

1. **Keyword Matching:**
   - Positive: "yes", "sure", "okay", "talk", "chat", "help", "please"
   - Negative: "no", "nope", "not", "don't", "can't", "won't", "stop"

2. **Grok Sentiment Analysis:**
   - Analyzes the sentiment of the response
   - Determines if user wants to talk

3. **Context Understanding:**
   - Considers the full response, not just keywords
   - Handles nuanced responses

## Call Initiation

When a user agrees to talk:

1. **Backend Preparation:**
   - Loads user context from original post
   - Retrieves conversation history
   - Gets relevant support resources via RAG
   - Generates personalized initial greeting

2. **Call Setup:**
   - Creates conversation ID
   - Prepares conversation context
   - Generates initial message

3. **Voice Call:**
   - Connects via Twilio
   - Uses xAI Grok Realtime API
   - Provides supportive, calming conversation

## Conversation Goals

During the call, the AI therapist focuses on:

1. **Making them feel heard** - Active listening and validation
2. **Helping them calm down** - Calming language and techniques
3. **Providing support** - Emotional support and encouragement
4. **Shifting perspective** - Toward hope and positivity
5. **Feeling better** - Overall goal is to help them "chill up" (calm down and feel better)

## Configuration

### Environment Variables

```bash
# Required
X_API_BEARER_TOKEN=your_twitter_token
GROK_API_KEY=your_grok_key

# Optional (for calling)
BACKEND_URL=http://localhost:8001
TELEPHONY_URL=http://localhost:3000
```

### Response Tracker Storage

Tracking data is stored in:
- `./response_tracking/user_responses.json`

You can customize the storage path:
```python
tracker = ResponseTracker(storage_path="./custom_path")
```

## Implementation Notes

### Twitter API Requirements

To fully implement response monitoring, you need:

1. **OAuth 1.0a Authentication:**
   - Bearer tokens alone cannot reply to tweets or check mentions
   - Requires user context OAuth for posting

2. **Mentions/Replies API:**
   - Monitor mentions of your account
   - Check replies to your tweets
   - Match responses to original offers

3. **Current Implementation:**
   - Reply functionality is simulated (logs what would be sent)
   - Response monitoring is a placeholder
   - In production, implement actual Twitter API calls

### Production Setup

For production use:

1. **Set up OAuth 1.0a:**
   ```python
   # Use tweepy or similar library
   import tweepy
   auth = tweepy.OAuth1UserHandler(
       consumer_key, consumer_secret,
       access_token, access_token_secret
   )
   api = tweepy.API(auth)
   ```

2. **Implement Reply Function:**
   ```python
   def reply_to_tweet(self, tweet_id: str, text: str):
       api.update_status(
           status=text,
           in_reply_to_status_id=tweet_id,
           auto_populate_reply_metadata=True
       )
   ```

3. **Monitor Mentions:**
   ```python
   def check_mentions(self):
       mentions = api.mentions_timeline()
       # Process mentions and match to offers
   ```

## Example Workflow

```bash
# 1. Scan and reply to negative posts
python analyze_and_support.py --query "feeling anxious" --max-posts 20

# Output:
# [1/20] Analyzing post by @user1...
#   ⚠️  Negative sentiment detected!
#   Severity: medium
#   Concerns: anxiety, stress
#   💬 Generating therapist offer reply...
#   📝 Reply: Hey @user1, I saw your post and I'm here if you'd like to talk...
#   ✅ Reply sent (or simulated)

# 2. Start monitoring (in another terminal)
python start_monitoring.py

# Output:
# Monitoring for user responses to therapist offers...
# [2024-01-01 12:05:00] Checking for user responses...
# [2024-01-01 12:10:00] ✅ @user1 wants to talk!
#    Response: yes please
#    📞 Call initiated successfully!
```

## Troubleshooting

### Replies Not Sending

- Check if OAuth 1.0a is configured
- Verify Twitter API permissions
- Check rate limits

### Responses Not Detected

- Implement actual mentions/replies monitoring
- Check response_tracker.py implementation
- Verify Twitter API access

### Calls Not Initiating

- Check backend is running (port 8001)
- Verify phone numbers are available
- Check telephony service is running (port 3000)
- Review call initiation logs

## Privacy and Ethics

**Important Considerations:**

1. **User Consent:** Users explicitly agree by replying "yes"
2. **Transparency:** Replies clearly state it's an AI therapist
3. **Privacy:** All conversations are stored securely
4. **Boundaries:** System suggests professional help when needed
5. **Opt-out:** Users can stop at any time

## Future Enhancements

1. **DM-based Communication:** Use DMs for more private conversations
2. **Scheduled Follow-ups:** Check in with users after calls
3. **Multi-language Support:** Reply in user's language
4. **Crisis Detection:** Immediate escalation for high-risk situations
5. **Analytics Dashboard:** Track response rates and outcomes

## Support

For issues or questions:
- Check logs in `./response_tracking/`
- Review Twitter API documentation
- Verify all services are running
- Check environment variables

