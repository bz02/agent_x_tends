#!/usr/bin/env python3
"""
Response Tracker - Monitors user responses to therapist offers and initiates calls
"""

import os
import json
import time
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path


class ResponseTracker:
    """Tracks user responses to therapist offers and manages call initiation"""
    
    def __init__(self, storage_path: str = "./response_tracking"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.tracking_file = self.storage_path / "user_responses.json"
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8001")
        self.telephony_url = os.getenv("TELEPHONY_URL", "http://localhost:3000")
        
        # Load existing tracking data
        self.tracking_data = self._load_tracking_data()
    
    def _load_tracking_data(self) -> Dict[str, Any]:
        """Load tracking data from file"""
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading tracking data: {e}")
        return {
            "offers_sent": {},
            "user_responses": {},
            "calls_initiated": {}
        }
    
    def _save_tracking_data(self):
        """Save tracking data to file"""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(self.tracking_data, f, indent=2)
        except Exception as e:
            print(f"Error saving tracking data: {e}")
    
    def record_offer_sent(self, user_id: str, username: str, tweet_id: str, reply_id: str):
        """Record that we sent a therapist offer to a user"""
        offer_key = f"{user_id}_{tweet_id}"
        self.tracking_data["offers_sent"][offer_key] = {
            "user_id": user_id,
            "username": username,
            "tweet_id": tweet_id,
            "reply_id": reply_id,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        self._save_tracking_data()
    
    def check_user_responses(self, twitter_client, grok_client) -> List[Dict[str, Any]]:
        """
        Check for user responses to our offers.
        This would typically monitor mentions or replies to our account.
        
        Returns:
            List of users who responded positively
        """
        # In a real implementation, you would:
        # 1. Get mentions/replies to your account
        # 2. Check if they're responding to our offers
        # 3. Analyze if the response is positive (yes, talk, etc.)
        
        positive_responses = []
        
        # For now, this is a placeholder that would need to be implemented
        # with actual Twitter API calls to check mentions/replies
        print("[INFO] Checking for user responses to therapist offers...")
        print("[INFO] In production, this would check mentions/replies via Twitter API")
        
        return positive_responses
    
    def analyze_response_sentiment(self, response_text: str, grok_client) -> bool:
        """
        Analyze if a user's response indicates they want to talk.
        
        Args:
            response_text: The user's reply text
            grok_client: Grok client for sentiment analysis
        
        Returns:
            True if response is positive, False otherwise
        """
        positive_indicators = ["yes", "sure", "okay", "ok", "talk", "chat", "help", "please", "would like"]
        negative_indicators = ["no", "nope", "not", "don't", "can't", "won't", "stop"]
        
        response_lower = response_text.lower()
        
        # Check for positive indicators
        has_positive = any(indicator in response_lower for indicator in positive_indicators)
        has_negative = any(indicator in response_lower for indicator in negative_indicators)
        
        # Use Grok for more nuanced analysis
        try:
            analysis = grok_client.analyze_sentiment(
                post_text=response_text,
                username=""
            )
            
            # If sentiment is positive and needs support, they likely want to talk
            if analysis.get("sentiment") == "positive" or (
                analysis.get("needs_support") and not has_negative
            ):
                return True
        except Exception as e:
            print(f"Error analyzing response: {e}")
        
        # Fallback to keyword matching
        return has_positive and not has_negative
    
    def initiate_call_for_user(
        self,
        user_id: str,
        username: str,
        phone_number: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Initiate a call to a user who agreed to talk.
        
        Args:
            user_id: Twitter user ID
            username: Twitter username
            phone_number: User's phone number (if available)
            context: Additional context about the user
        
        Returns:
            Call initiation result or None
        """
        if not phone_number:
            print(f"[WARNING] No phone number for @{username}. Cannot initiate call.")
            print(f"[INFO] User would need to provide phone number via DM or other method")
            return None
        
        try:
            # Call backend to prepare conversation
            response = requests.post(
                f"{self.backend_url}/api/calls/initiate",
                json={
                    "user_id": user_id,
                    "username": username,
                    "phone_number": phone_number,
                    "context": context or {}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Record the call initiation
                call_key = f"{user_id}_{int(time.time())}"
                self.tracking_data["calls_initiated"][call_key] = {
                    "user_id": user_id,
                    "username": username,
                    "conversation_id": result.get("conversation_id"),
                    "phone_number": phone_number,
                    "timestamp": datetime.now().isoformat(),
                    "status": "initiated"
                }
                self._save_tracking_data()
                
                print(f"✅ Call initiated for @{username}")
                print(f"   Conversation ID: {result.get('conversation_id')}")
                print(f"   Initial message: {result.get('initial_message', '')[:100]}...")
                
                return result
            else:
                print(f"❌ Error initiating call: {response.status_code} {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error initiating call: {e}")
            return None
    
    def get_pending_offers(self) -> List[Dict[str, Any]]:
        """Get list of pending offers (users we've contacted but haven't responded)"""
        pending = []
        for key, offer in self.tracking_data["offers_sent"].items():
            if offer.get("status") == "pending":
                # Check if offer is still recent (within 7 days)
                timestamp = datetime.fromisoformat(offer["timestamp"])
                if datetime.now() - timestamp < timedelta(days=7):
                    pending.append(offer)
        return pending
    
    def mark_offer_responded(self, user_id: str, tweet_id: str, response: str, wants_to_talk: bool):
        """Mark that a user responded to our offer"""
        offer_key = f"{user_id}_{tweet_id}"
        if offer_key in self.tracking_data["offers_sent"]:
            self.tracking_data["offers_sent"][offer_key]["status"] = "responded"
            self.tracking_data["offers_sent"][offer_key]["response"] = response
            self.tracking_data["offers_sent"][offer_key]["wants_to_talk"] = wants_to_talk
            self.tracking_data["offers_sent"][offer_key]["response_timestamp"] = datetime.now().isoformat()
            self._save_tracking_data()


def monitor_and_call(
    twitter_client,
    grok_client,
    response_tracker: ResponseTracker,
    check_interval: int = 300  # Check every 5 minutes
):
    """
    Continuously monitor for user responses and initiate calls.
    
    Args:
        twitter_client: Twitter API client
        grok_client: Grok API client
        response_tracker: ResponseTracker instance
        check_interval: Seconds between checks
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting response monitoring...")
    print(f"Checking every {check_interval} seconds...")
    
    while True:
        try:
            # Check for responses
            responses = response_tracker.check_user_responses(twitter_client, grok_client)
            
            for response in responses:
                user_id = response.get("user_id")
                username = response.get("username")
                response_text = response.get("text", "")
                tweet_id = response.get("tweet_id")
                
                # Analyze if they want to talk
                wants_to_talk = response_tracker.analyze_response_sentiment(
                    response_text,
                    grok_client
                )
                
                if wants_to_talk:
                    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
                    print(f"✅ @{username} wants to talk!")
                    print(f"   Response: {response_text[:100]}")
                    
                    # Mark as responded
                    response_tracker.mark_offer_responded(
                        user_id, tweet_id, response_text, True
                    )
                    
                    # Get phone number (in production, this might come from DM or user profile)
                    phone_number = response.get("phone_number")
                    
                    # Initiate call
                    call_result = response_tracker.initiate_call_for_user(
                        user_id=user_id,
                        username=username,
                        phone_number=phone_number,
                        context=response.get("context", {})
                    )
                    
                    if call_result:
                        print(f"   📞 Call initiated successfully!")
                    else:
                        print(f"   ⚠️  Could not initiate call (phone number may be needed)")
                else:
                    print(f"   @{username} responded but doesn't want to talk right now")
                    response_tracker.mark_offer_responded(
                        user_id, tweet_id, response_text, False
                    )
            
            # Wait before next check
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            print("\n[INFO] Monitoring stopped by user")
            break
        except Exception as e:
            print(f"[ERROR] Error in monitoring loop: {e}")
            time.sleep(check_interval)


if __name__ == "__main__":
    from analyze_and_support import TwitterClient, GrokClient
    
    # Initialize clients
    twitter_client = TwitterClient(os.getenv("X_API_BEARER_TOKEN", ""))
    grok_client = GrokClient(os.getenv("GROK_API_KEY", ""))
    tracker = ResponseTracker()
    
    # Start monitoring
    monitor_and_call(twitter_client, grok_client, tracker)

