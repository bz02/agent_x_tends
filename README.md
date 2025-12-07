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

