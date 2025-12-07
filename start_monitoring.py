#!/usr/bin/env python3
"""
Start monitoring for user responses and initiate calls automatically.
Run this after scan_and_analyze.py has sent offers to users.
"""

import os
import sys
from dotenv import load_dotenv
from analyze_and_support import TwitterClient, GrokClient
from response_tracker import monitor_and_call, ResponseTracker

load_dotenv()

def main():
    """Main function to start monitoring"""
    print("=" * 60)
    print("Voice Support - Response Monitoring")
    print("=" * 60)
    print()
    
    # Get API credentials
    bearer_token = os.getenv("X_API_BEARER_TOKEN")
    grok_api_key = os.getenv("GROK_API_KEY")
    
    if not bearer_token:
        print("Error: X_API_BEARER_TOKEN environment variable is required.", file=sys.stderr)
        sys.exit(1)
    
    if not grok_api_key:
        print("Error: GROK_API_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)
    
    # Initialize clients
    twitter_client = TwitterClient(bearer_token)
    grok_client = GrokClient(grok_api_key)
    tracker = ResponseTracker()
    
    print("Monitoring for user responses to therapist offers...")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        # Start monitoring (checks every 5 minutes by default)
        monitor_and_call(
            twitter_client=twitter_client,
            grok_client=grok_client,
            response_tracker=tracker,
            check_interval=300  # 5 minutes
        )
    except KeyboardInterrupt:
        print("\n[INFO] Monitoring stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

