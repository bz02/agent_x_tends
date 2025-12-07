#!/usr/bin/env python3
"""
Script to scan Twitter posts, analyze sentiment using Grok, and provide positive support.

Usage:
    python analyze_and_support.py [--query QUERY] [--max-posts N] [--dry-run]

Environment Variables:
    X_API_BEARER_TOKEN: Your X API Bearer token
    GROK_API_KEY: Your xAI Grok API key
"""

import os
import sys
import argparse
import requests
import time
import json
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path


class GrokClient:
    """Client for interacting with xAI Grok API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def analyze_sentiment(self, post_text: str, username: str = "") -> Dict[str, Any]:
        """
        Analyze sentiment of a post using Grok.
        
        Args:
            post_text: The text content of the post
            username: Optional username for context
        
        Returns:
            Dictionary with sentiment analysis results
        """
        prompt = f"""Analyze the sentiment of this Twitter post and determine if it contains negative thoughts, 
depression, anxiety, or distress. Consider the context carefully.

Post by @{username if username else 'user'}: {post_text}

Respond in JSON format with:
{{
    "is_negative": true/false,
    "sentiment": "positive/negative/neutral",
    "severity": "low/medium/high",
    "concerns": ["list", "of", "concerns"],
    "needs_support": true/false,
    "reasoning": "brief explanation"
}}"""

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": "grok-4-0709",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a compassionate mental health awareness assistant. Analyze posts carefully and identify those that may need support."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract the response content
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Try to parse JSON from the response
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                analysis = json.loads(content)
                return analysis
            except json.JSONDecodeError:
                # Fallback: parse the response text
                return {
                    "is_negative": "negative" in content.lower() or "true" in content.lower(),
                    "sentiment": "negative" if "negative" in content.lower() else "neutral",
                    "severity": "medium",
                    "concerns": [],
                    "needs_support": True,
                    "reasoning": content[:200]
                }
                
        except requests.exceptions.RequestException as e:
            print(f"Error calling Grok API: {e}", file=sys.stderr)
            return {
                "is_negative": False,
                "sentiment": "unknown",
                "severity": "low",
                "concerns": [],
                "needs_support": False,
                "reasoning": f"API error: {str(e)}"
            }
    
    def generate_support_message(self, post_text: str, username: str, concerns: List[str]) -> str:
        """
        Generate a supportive, positive message using Grok.
        
        Args:
            post_text: The original post text
            username: The username to address
            concerns: List of identified concerns
        
        Returns:
            A supportive message
        """
        concerns_str = ", ".join(concerns) if concerns else "general distress"
        
        prompt = f"""Generate a warm, compassionate, and supportive direct message to send to @{username} on Twitter.
They posted: "{post_text}"

The post shows concerns about: {concerns_str}

Create a message that:
- Is genuine, empathetic, and non-intrusive
- Offers support without being preachy
- Is positive and encouraging
- Respects their privacy and feelings
- Is appropriate for a Twitter DM (max 280 characters, but can be slightly longer if needed)
- Does NOT mention that this is automated or AI-generated
- Feels like a caring human reaching out

Write only the message text, nothing else."""

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": "grok-4-0709",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a compassionate person who reaches out to help others. Write warm, genuine messages."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 200
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            message = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
            # Clean up the message
            message = message.replace('"', '').strip()
            if message.startswith("@"):
                message = message[1:]
            
            return message if message else "Hey, I saw your post and wanted to reach out. If you need someone to talk to, I'm here. You're not alone, and things can get better. 💙"
            
        except requests.exceptions.RequestException as e:
            print(f"Error generating support message: {e}", file=sys.stderr)
            return f"Hey @{username}, I saw your post and wanted to reach out. If you need someone to talk to, I'm here. You're not alone. 💙"


class TwitterClient:
    """Client for interacting with X (Twitter) API."""
    
    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.base_url = "https://api.x.com/2"
        self.headers = {
            "Authorization": f"Bearer {bearer_token}"
        }
    
    def search_posts(self, query: str = "", max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Search for recent posts on Twitter.
        
        Args:
            query: Search query (if empty, uses default: recent English posts)
            max_results: Maximum number of results (10-100)
        
        Returns:
            List of post dictionaries
        """
        url = f"{self.base_url}/tweets/search/all"
        #tweets/search/all?max_results=10
        
        # Query parameter is required for search endpoint
        # If no query provided, use a default query to get recent posts
        # Using a simple query that should work: get recent English posts that are not retweets
        if not query or query.strip() == "":
            # Default query: recent English posts, not retweets, from last 7 days
            query = "lang:en -is:retweet"
        
        # Ensure max_results is within valid range (10-100)
        max_results = max(10, min(max_results, 100))
        
        # Build parameters according to X API v2 documentation
        # Reference: https://docs.x.com/x-api/fundamentals/data-dictionary
        params = {
            "query": query,
            "max_results": max_results,
            "tweet.fields": "created_at,author_id,public_metrics,text",
            "user.fields": "username,name,description,public_metrics",
            "expansions": "author_id"
        }
        
        try:
            # Debug: print the request URL (without showing the token)
            if os.getenv("DEBUG_API_CALLS", "").lower() == "true":
                from urllib.parse import urlencode
                debug_url = f"{url}?{urlencode(params)}"
                print(f"[DEBUG] Request URL: {debug_url}", file=sys.stderr)
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Check for errors in response
            if "errors" in data:
                error_messages = [err.get("message", "Unknown error") for err in data["errors"]]
                print(f"API Errors: {', '.join(error_messages)}", file=sys.stderr)
                return []
            
            posts = []
            users = {}
            
            # Extract users from includes
            if "includes" in data and "users" in data["includes"]:
                users = {user["id"]: user for user in data["includes"]["users"]}
            
            # Extract tweets from data
            if "data" in data:
                for tweet in data["data"]:
                    author_id = tweet.get("author_id")
                    user = users.get(author_id, {})
                    
                    posts.append({
                        "id": tweet.get("id"),
                        "text": tweet.get("text", ""),
                        "author_id": author_id,
                        "username": user.get("username", "unknown"),
                        "name": user.get("name", "Unknown"),
                        "created_at": tweet.get("created_at"),
                        "metrics": tweet.get("public_metrics", {})
                    })
            
            return posts
            
        except requests.exceptions.HTTPError as e:
            # Try to get detailed error information
            if hasattr(e.response, 'json'):
                try:
                    error_data = e.response.json()
                    if "errors" in error_data:
                        for error in error_data["errors"]:
                            print(f"API Error {error.get('code', 'unknown')}: {error.get('message', 'No message')}", file=sys.stderr)
                            if "details" in error:
                                print(f"  Details: {error['details']}", file=sys.stderr)
                    else:
                        print(f"Error response: {error_data}", file=sys.stderr)
                except:
                    if hasattr(e.response, 'text'):
                        print(f"Error response text: {e.response.text[:500]}", file=sys.stderr)
            
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                if status_code == 401:
                    print("Authentication failed. Please check your Bearer token.", file=sys.stderr)
                elif status_code == 400:
                    print("Bad Request. Check your query syntax and parameters.", file=sys.stderr)
                    print(f"Query used: {query}", file=sys.stderr)
                elif status_code == 429:
                    print("Rate limit exceeded. Please wait before trying again.", file=sys.stderr)
                else:
                    print(f"HTTP Error {status_code}: {e}", file=sys.stderr)
            else:
                print(f"HTTP Error: {e}", file=sys.stderr)
            return []
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}", file=sys.stderr)
            return []
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information by user ID.
        
        Args:
            user_id: Twitter user ID
        
        Returns:
            User information dictionary
        """
        url = f"{self.base_url}/users/{user_id}"
        
        params = {
            "user.fields": "username,name,description,public_metrics,location,url"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json().get("data", {})
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user info: {e}", file=sys.stderr)
            return None
    
    def send_direct_message(self, user_id: str, message: str) -> bool:
        """
        Send a direct message to a user.
        
        Args:
            user_id: Twitter user ID to send message to
            message: Message text
        
        Returns:
            True if successful, False otherwise
        """
        # Note: This requires OAuth 1.0a with user context, not just Bearer token
        # For now, we'll return False and log that this requires additional setup
        print(f"[INFO] DM functionality requires OAuth 1.0a with user context.")
        print(f"[INFO] Would send to user_id {user_id}: {message[:100]}...")
        return False
    
    def find_contact_info(self, user_id: str) -> Dict[str, Any]:
        """
        Find contact information for a user.
        
        Args:
            user_id: Twitter user ID
        
        Returns:
            Dictionary with available contact information
        """
        user_info = self.get_user_info(user_id)
        
        if not user_info:
            return {}
        
        contact_info = {
            "username": user_info.get("username"),
            "name": user_info.get("name"),
            "description": user_info.get("description", ""),
            "location": user_info.get("location"),
            "url": user_info.get("url"),
            "profile_url": f"https://twitter.com/{user_info.get('username')}" if user_info.get("username") else None
        }
        
        return contact_info


def scan_and_analyze(
    twitter_client: TwitterClient,
    grok_client: GrokClient,
    query: str = "",
    max_posts: int = 50,
    dry_run: bool = False
) -> List[Dict[str, Any]]:
    """
    Main function to scan posts, analyze sentiment, and provide support.
    
    Args:
        twitter_client: Twitter API client
        grok_client: Grok API client
        query: Search query for posts
        max_posts: Maximum number of posts to scan
        dry_run: If True, don't send messages
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting scan...")
    print(f"Query: {query if query else 'Recent posts'}")
    print(f"Max posts: {max_posts}")
    print(f"Dry run: {dry_run}\n")
    
    # Search for posts
    print("Searching for posts...")
    posts = twitter_client.search_posts(query=query, max_results=max_posts)
    
    if not posts:
        print("No posts found.")
        return []
    
    print(f"Found {len(posts)} posts. Analyzing sentiment...\n")
    
    negative_posts = []
    
    # Analyze each post
    for idx, post in enumerate(posts, 1):
        print(f"[{idx}/{len(posts)}] Analyzing post by @{post['username']}...")
        
        # Analyze sentiment
        analysis = grok_client.analyze_sentiment(
            post_text=post["text"],
            username=post["username"]
        )
        
        if analysis.get("is_negative") and analysis.get("needs_support"):
            print(f"  ⚠️  Negative sentiment detected!")
            print(f"  Severity: {analysis.get('severity', 'unknown')}")
            print(f"  Concerns: {', '.join(analysis.get('concerns', []))}")
            
            negative_posts.append({
                "post": post,
                "analysis": analysis
            })
        
        # Rate limiting - be respectful
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print(f"Found {len(negative_posts)} posts needing support")
    print(f"{'='*60}\n")
    
    # Save results to file
    results_file = f"support_outreach_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results_data = []
    
    # Process negative posts
    for idx, item in enumerate(negative_posts, 1):
        post = item["post"]
        analysis = item["analysis"]
        
        print(f"[{idx}/{len(negative_posts)}] Processing @{post['username']}...")
        
        # Find contact info
        contact_info = twitter_client.find_contact_info(post["author_id"])
        print(f"  Contact: @{contact_info.get('username', 'unknown')}")
        if contact_info.get("profile_url"):
            print(f"  Profile: {contact_info['profile_url']}")
        
        # Generate support message
        print("  Generating support message...")
        support_message = grok_client.generate_support_message(
            post_text=post["text"],
            username=post["username"],
            concerns=analysis.get("concerns", [])
        )
        
        print(f"  Message: {support_message[:100]}...")
        
        # Prepare result data
        result_entry = {
            "username": contact_info.get("username"),
            "user_id": post["author_id"],
            "profile_url": contact_info.get("profile_url"),
            "original_post": post["text"],
            "post_url": f"https://twitter.com/{contact_info.get('username')}/status/{post['id']}" if post.get("id") else None,
            "sentiment_analysis": analysis,
            "support_message": support_message,
            "contact_info": contact_info,
            "timestamp": datetime.now().isoformat()
        }
        results_data.append(result_entry)
        
        # Send message (or simulate)
        if not dry_run:
            # Note: Sending DMs requires OAuth 1.0a with user context
            # This is a limitation of the Twitter API
            print("  ⚠️  Note: DM sending requires OAuth 1.0a authentication.")
            print(f"  📧 Contact info saved for manual outreach:")
            print(f"     Username: @{contact_info.get('username')}")
            print(f"     Profile: {contact_info.get('profile_url')}")
            print(f"     Suggested message: {support_message}")
        else:
            print("  [DRY RUN] Would send message")
        
        print()
        
        # Rate limiting
        time.sleep(2)
    
    # Save results to JSON file
    if results_data:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "scan_timestamp": datetime.now().isoformat(),
                "query": query,
                "total_posts_scanned": len(posts),
                "negative_posts_found": len(negative_posts),
                "results": results_data
            }, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {results_file}")
        print(f"   This file contains all contact information and suggested messages for outreach.")
    
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scan complete!")
    
    return results_data


def main():
    """Main function to handle command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Scan Twitter posts, analyze sentiment with Grok, and provide support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan recent posts (default)
  python analyze_and_support.py
  
  # Search for specific query
  python analyze_and_support.py --query "feeling sad"
  
  # Limit number of posts
  python analyze_and_support.py --max-posts 20
  
  # Dry run (don't send messages)
  python analyze_and_support.py --dry-run

Environment Variables:
  X_API_BEARER_TOKEN: Your X API Bearer token
  GROK_API_KEY: Your xAI Grok API key
        """
    )
    
    parser.add_argument(
        "--query",
        type=str,
        default="",
        help="Search query for posts (default: recent posts)"
    )
    
    parser.add_argument(
        "--max-posts",
        type=int,
        default=50,
        help="Maximum number of posts to scan (default: 50)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - don't send messages"
    )
    
    args = parser.parse_args()
    
    # Get API credentials
    bearer_token = os.getenv("X_API_BEARER_TOKEN")
    grok_api_key = os.getenv("GROK_API_KEY")
    
    if not bearer_token:
        print("Error: X_API_BEARER_TOKEN environment variable is required.", file=sys.stderr)
        sys.exit(1)
    
    if not grok_api_key:
        print("Error: GROK_API_KEY environment variable is required.", file=sys.stderr)
        print("Get your API key from: https://console.x.ai/", file=sys.stderr)
        sys.exit(1)
    
    # Initialize clients
    twitter_client = TwitterClient(bearer_token)
    grok_client = GrokClient(grok_api_key)
    
    try:
        scan_and_analyze(
            twitter_client=twitter_client,
            grok_client=grok_client,
            query=args.query,
            max_posts=args.max_posts,
            dry_run=args.dry_run
        )
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

