# X Trends Fetcher

A Python script to fetch trending topics from X (Twitter) using the X API v2.

## Features

- Fetch trends by WOEID (Where On Earth ID)
- Configurable number of trends (1-50)
- Secure token handling via environment variables
- Pretty-printed output
- Error handling and validation

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Set your Bearer token as an environment variable (recommended)
export X_API_BEARER_TOKEN=your_token_here

# Fetch trends for a specific WOEID
python fetch_x_trends.py 1  # Worldwide trends
```

### Command-Line Options

```bash
python fetch_x_trends.py <woeid> [options]

Options:
  --max-trends N    Maximum number of trends (1-50, default: 20)
  --token TOKEN     X API Bearer token (or use X_API_BEARER_TOKEN env var)
  --fields FIELDS   Fields to include: trend_name, tweet_count
```

### Examples

```bash
# Fetch top 10 trends for the United States
python fetch_x_trends.py 23424977 --max-trends 10

# Use token from command line
python fetch_x_trends.py 1 --token YOUR_TOKEN_HERE

# Fetch trends for United Kingdom
python fetch_x_trends.py 23424975
```

## Common WOEIDs

- `1` - Worldwide
- `23424977` - United States
- `23424975` - United Kingdom
- `23424748` - Canada
- `23424829` - Germany
- `23424856` - Japan

You can find more WOEIDs using the [Yahoo GeoPlanet API](https://developer.yahoo.com/geo/geoplanet/) or search online.

## Getting Your Bearer Token

1. Go to [X Developer Portal](https://developer.x.com/)
2. Create a new app or use an existing one
3. Navigate to "Keys and tokens"
4. Generate a Bearer Token
5. Copy the token and set it as an environment variable:
   ```bash
   export X_API_BEARER_TOKEN=your_token_here
   ```

## API Reference

This script uses the [X API v2 Get Trends by WOEID endpoint](https://docs.x.com/x-api/trends/get-trends-by-woeid).

## Error Handling

The script handles common errors:
- Authentication failures (401)
- Invalid WOEID (404)
- Network errors
- API rate limits

## License

This script is provided as-is for educational and personal use.

---

# Twitter Post Sentiment Analysis & Support

A Python script to scan Twitter posts, analyze sentiment using Grok AI, and provide positive support to users with negative thoughts.

## Features

- Scan Twitter posts using search queries or recent posts
- Analyze sentiment using xAI Grok model to detect negative thoughts
- Identify users who may need support
- Generate compassionate support messages using Grok
- Find user contact information (profile, username)
- Rate limiting and respectful API usage

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up API credentials:
```bash
export X_API_BEARER_TOKEN=your_twitter_token_here
export GROK_API_KEY=your_grok_api_key_here
```

## Usage

### Basic Usage

```bash
# Scan recent posts (default: 50 posts)
python analyze_and_support.py

# Search for specific keywords
python analyze_and_support.py --query "feeling sad"

# Limit number of posts to scan
python analyze_and_support.py --max-posts 20

# Dry run (analyze but don't send messages)
python analyze_and_support.py --dry-run
```

### Command-Line Options

```bash
python analyze_and_support.py [options]

Options:
  --query QUERY      Search query for posts (default: recent posts)
  --max-posts N      Maximum number of posts to scan (default: 50)
  --dry-run          Dry run mode - analyze but don't send messages
```

### Examples

```bash
# Scan for posts about anxiety
python analyze_and_support.py --query "anxiety OR stressed OR overwhelmed"

# Scan 100 recent posts
python analyze_and_support.py --max-posts 100

# Test run without sending messages
python analyze_and_support.py --query "feeling down" --dry-run
```

## Getting API Keys

### Twitter/X API Bearer Token

1. Go to [X Developer Portal](https://developer.x.com/)
2. Create a new app or use an existing one
3. Navigate to "Keys and tokens"
4. Generate a Bearer Token
5. Set as environment variable:
   ```bash
   export X_API_BEARER_TOKEN=your_token_here
   ```

### Grok API Key

1. Go to [xAI Console](https://console.x.ai/)
2. Sign up or log in
3. Navigate to API keys section
4. Generate a new API key
5. Set as environment variable:
   ```bash
   export GROK_API_KEY=your_key_here
   ```

## How It Works

1. **Post Scanning**: Searches Twitter for posts based on your query or recent posts
2. **Sentiment Analysis**: Uses Grok AI to analyze each post for negative sentiment, depression, anxiety, or distress
3. **Contact Finding**: Retrieves user profile information and contact details
4. **Message Generation**: Uses Grok to generate compassionate, personalized support messages
5. **Outreach**: Provides contact information and suggested messages for manual outreach

## Important Notes

- **DM Sending**: Automated DM sending requires OAuth 1.0a authentication with user context, which is more complex to set up. The script currently provides contact information and suggested messages for manual outreach.
- **Rate Limiting**: The script includes rate limiting to respect API limits. Be mindful of Twitter and Grok API rate limits.
- **Privacy**: Always respect user privacy and Twitter's Terms of Service when reaching out to users.
- **Ethical Use**: Use this tool responsibly and with genuine intent to help others. Automated messaging should be used carefully and ethically.

## Output

The script provides:
- Analysis results for each post
- List of posts with negative sentiment
- User contact information (username, profile URL)
- Generated support messages
- Summary of findings

## Error Handling

The script handles:
- Authentication failures
- API rate limits
- Network errors
- Invalid responses
- JSON parsing errors

## License

This script is provided as-is for educational and personal use. Use responsibly and in accordance with Twitter's Terms of Service and API usage policies.

