#!/usr/bin/env python3
"""
Script to fetch X (Twitter) trends by WOEID using the X API v2.

Usage:
    python fetch_x_trends.py <woeid> [--max-trends N] [--token TOKEN]

Environment Variables:
    X_API_BEARER_TOKEN: Your X API Bearer token (recommended for security)
"""

import os
import sys
import argparse
import requests
from typing import Optional, Dict, List, Any


def fetch_trends_by_woeid(
    woeid: int,
    bearer_token: str,
    max_trends: int = 20,
    trend_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Fetch trending topics for a specific location by WOEID.
    
    Args:
        woeid: The WOEID (Where On Earth ID) of the location
        bearer_token: X API Bearer token for authentication
        max_trends: Maximum number of trends to return (1-50, default: 20)
        trend_fields: List of fields to include (e.g., ['trend_name', 'tweet_count'])
    
    Returns:
        Dictionary containing the API response with trends data
    
    Raises:
        requests.exceptions.RequestException: If the API request fails
    """
    url = f"https://api.x.com/2/trends/by/woeid/{woeid}"
    
    headers = {
        "Authorization": f"Bearer {bearer_token}"
    }
    
    params = {
        "max_trends": max_trends
    }
    
    if trend_fields:
        params["trend.fields"] = ",".join(trend_fields)
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}", file=sys.stderr)
        if response.status_code == 401:
            print("Authentication failed. Please check your Bearer token.", file=sys.stderr)
        elif response.status_code == 404:
            print(f"WOEID {woeid} not found.", file=sys.stderr)
        try:
            error_data = response.json()
            print(f"Error details: {error_data}", file=sys.stderr)
        except:
            print(f"Response: {response.text}", file=sys.stderr)
        raise
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}", file=sys.stderr)
        raise


def print_trends(data: Dict[str, Any]) -> None:
    """
    Pretty print the trends data.
    
    Args:
        data: The API response dictionary
    """
    if "errors" in data and data["errors"]:
        print("Errors occurred:")
        for error in data["errors"]:
            print(f"  - {error.get('title', 'Unknown error')}: {error.get('detail', 'No details')}")
        print()
    
    if "data" in data and data["data"]:
        print(f"Found {len(data['data'])} trending topics:\n")
        print(f"{'Rank':<6} {'Trend Name':<50} {'Tweet Count':<15}")
        print("-" * 75)
        
        for idx, trend in enumerate(data["data"], 1):
            trend_name = trend.get("trend_name", "N/A")
            tweet_count = trend.get("tweet_count", "N/A")
            print(f"{idx:<6} {trend_name:<50} {tweet_count:<15}")
    else:
        print("No trends data found.")


def main():
    """Main function to handle command-line arguments and fetch trends."""
    parser = argparse.ArgumentParser(
        description="Fetch X (Twitter) trends by WOEID",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch trends for WOEID 1 (Worldwide)
  python fetch_x_trends.py 1
  
  # Fetch top 10 trends
  python fetch_x_trends.py 1 --max-trends 10
  
  # Use token from command line
  python fetch_x_trends.py 1 --token YOUR_TOKEN_HERE
  
  # Use token from environment variable (recommended)
  export X_API_BEARER_TOKEN=YOUR_TOKEN_HERE
  python fetch_x_trends.py 1

Common WOEIDs:
  1 - Worldwide
  23424977 - United States
  23424975 - United Kingdom
  23424748 - Canada
  23424829 - Germany
  23424856 - Japan
        """
    )
    
    parser.add_argument(
        "woeid",
        type=int,
        help="WOEID (Where On Earth ID) of the location"
    )
    
    parser.add_argument(
        "--max-trends",
        type=int,
        default=20,
        choices=range(1, 51),
        metavar="N",
        help="Maximum number of trends to return (1-50, default: 20)"
    )
    
    parser.add_argument(
        "--token",
        type=str,
        help="X API Bearer token (or set X_API_BEARER_TOKEN environment variable)"
    )
    
    parser.add_argument(
        "--fields",
        nargs="+",
        choices=["trend_name", "tweet_count"],
        default=["trend_name", "tweet_count"],
        help="Fields to include in response (default: both)"
    )
    
    args = parser.parse_args()
    
    # Get bearer token from argument or environment variable
    bearer_token = args.token or os.getenv("X_API_BEARER_TOKEN")
    
    if not bearer_token:
        print("Error: Bearer token is required.", file=sys.stderr)
        print("Set X_API_BEARER_TOKEN environment variable or use --token option.", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Fetch trends
        result = fetch_trends_by_woeid(
            woeid=args.woeid,
            bearer_token=bearer_token,
            max_trends=args.max_trends,
            trend_fields=args.fields
        )
        
        # Print results
        print_trends(result)
        
    except requests.exceptions.RequestException:
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

