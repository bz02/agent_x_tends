#!/usr/bin/env python3
"""
Helper script to initiate a call to a user via Twilio
"""

import os
import sys
import requests
import json
from typing import Optional

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("Warning: twilio library not installed. Install with: pip install twilio")


def initiate_twilio_call(
    user_phone: str,
    twilio_phone: str,
    webhook_url: str,
    user_id: Optional[str] = None
) -> bool:
    """
    Initiate a Twilio call to a user.
    
    Args:
        user_phone: Phone number to call (E.164 format, e.g., +1234567890)
        twilio_phone: Your Twilio phone number
        webhook_url: URL for Twilio webhook (should point to /twiml endpoint)
        user_id: Optional user ID to pass to webhook
    
    Returns:
        True if successful, False otherwise
    """
    if not TWILIO_AVAILABLE:
        print("Error: Twilio library not installed")
        print("Install with: pip install twilio")
        return False
    
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    if not account_sid or not auth_token:
        print("Error: TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set")
        return False
    
    try:
        client = Client(account_sid, auth_token)
        
        # Add user_id to webhook URL if provided
        if user_id:
            separator = "&" if "?" in webhook_url else "?"
            webhook_url = f"{webhook_url}{separator}user_id={user_id}"
        
        call = client.calls.create(
            to=user_phone,
            from_=twilio_phone,
            url=webhook_url
        )
        
        print(f"✅ Call initiated!")
        print(f"   Call SID: {call.sid}")
        print(f"   Status: {call.status}")
        print(f"   To: {user_phone}")
        print(f"   From: {twilio_phone}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initiating call: {e}")
        return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Initiate a Twilio call to a user"
    )
    
    parser.add_argument(
        "--user-phone",
        required=True,
        help="Phone number to call (E.164 format, e.g., +1234567890)"
    )
    
    parser.add_argument(
        "--twilio-phone",
        required=True,
        help="Your Twilio phone number"
    )
    
    parser.add_argument(
        "--webhook-url",
        default=os.getenv("TWILIO_WEBHOOK_URL", "https://your-ngrok-domain.ngrok.app/twiml"),
        help="Webhook URL for Twilio (default: from TWILIO_WEBHOOK_URL env var)"
    )
    
    parser.add_argument(
        "--user-id",
        help="User ID to pass to webhook for context"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success = initiate_twilio_call(
        user_phone=args.user_phone,
        twilio_phone=args.twilio_phone,
        webhook_url=args.webhook_url,
        user_id=args.user_id
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

