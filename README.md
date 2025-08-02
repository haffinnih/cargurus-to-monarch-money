# CarGurus to Monarch Money Vehicle Value Scraper

A Python script that extracts daily vehicle price data from CarGurus API and formats it for import into Monarch Money's vehicle tracking system.

## Features

- Extracts historical vehicle price data from CarGurus
- Outputs CSV files compatible with Monarch Money import format
- Handles date range chunking automatically for granular data
- Forward-fills missing data points to maintain continuity
- Comprehensive input validation and error handling
- Rate limiting to respect API constraints

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. Make sure you have uv installed.

```bash
# Clone or download the project
cd car-gurus-value

# Install dependencies
uv sync
```

## Usage

### Basic Command

```bash
uv run python cargurus_scraper.py \
  --entity-id "c32015" \
  --model-path "Honda-Civic-Hatchback-d2441" \
  --start-date "2024-01-01" \
  --end-date "2024-06-30" \
  --account-name "2022 Honda Civic EX-L" \
  --session-cookie "ABC123XYZ456"
```

### Parameters

| Parameter          | Description                     | Example                       |
| ------------------ | ------------------------------- | ----------------------------- |
| `--entity-id`      | CarGurus vehicle entity ID      | `c32015`                      |
| `--model-path`     | URL path segment from CarGurus  | `Honda-Civic-Hatchback-d2441` |
| `--start-date`     | Start date in YYYY-MM-DD format | `2024-01-01`                  |
| `--end-date`       | End date in YYYY-MM-DD format   | `2024-12-31`                  |
| `--account-name`   | Vehicle name for CSV output     | `2022 Honda Civic EX-L`       |
| `--session-cookie` | JSESSIONID cookie from CarGurus | `ABC123XYZ456`                |

### Getting Required Parameters

#### 1. Finding Entity ID and Model Path

1. Go to CarGurus and search for your vehicle
2. Navigate to the price trends page for your specific model
3. The URL will look like: `https://www.cargurus.com/research/price-trends/Honda-Civic-Hatchback-d2441`
4. The model path is: `Honda-Civic-Hatchback-d2441`
5. Open browser developer tools and inspect the network requests
6. Look for API calls to find the entity ID (e.g., `c32015`)

#### 2. Getting Session Cookie

1. Open CarGurus in your browser and log in if required
2. Open browser developer tools (F12)
3. Go to Application/Storage tab → Cookies → cargurus.com
4. Find the `JSESSIONID` cookie value
5. Copy the value (without "JSESSIONID=")

## Output

The script generates a CSV file with the following format:

```csv
Date,Balance,Account
2024-01-01,24988.09,2022 Honda Civic EX-L
2024-01-02,24988.09,2022 Honda Civic EX-L
2024-01-03,24979.12,2022 Honda Civic EX-L
```

**File naming:** `{account_name_sanitized}_{start_date}_{end_date}.csv`

Example: `2022_Honda_Civic_EX-L_2024-01-01_2024-06-30.csv`

## Import to Monarch Money

1. Log into Monarch Money
2. Go to Settings → Data Import
3. Upload the generated CSV file
4. Map the columns:
   - Date → Date
   - Balance → Balance/Value
   - Account → Account Name

## Error Handling

The script provides clear error messages for common issues:

- **Invalid date format:** "Error: Date must be in YYYY-MM-DD format"
- **Date range issues:** "Error: Start date cannot be more than 1 year ago"
- **Missing parameters:** "Error: Missing required parameter: entity_id"
- **Invalid session:** "Error: Invalid session cookie. Please provide a valid JSESSIONID"
- **No data found:** "Error: No price data available for the specified vehicle and date range"

## Limitations

- Start date cannot be more than 1 year ago (CarGurus API limitation)
- Requires valid JSESSIONID cookie from an active CarGurus session
- Rate limited to prevent overwhelming the API
- Data availability depends on CarGurus having price information for your vehicle

## Examples

### Tesla Model 3

```bash
uv run python cargurus_scraper.py \
  --entity-id "c26989" \
  --model-path "Tesla-Model-3-d2115" \
  --start-date "2024-01-01" \
  --end-date "2024-03-31" \
  --account-name "2023 Tesla Model 3" \
  --session-cookie "your_session_cookie_here"
```

### Toyota Camry

```bash
uv run python cargurus_scraper.py \
  --entity-id "c25847" \
  --model-path "Toyota-Camry-d15" \
  --start-date "2024-06-01" \
  --end-date "2024-08-31" \
  --account-name "2022 Toyota Camry LE" \
  --session-cookie "your_session_cookie_here"
```

## Troubleshooting

### "Invalid session cookie" error

- Your JSESSIONID cookie has expired
- Get a fresh cookie by logging into CarGurus again

### "Rate limited" error

- Wait a few minutes and try again
- The script includes built-in rate limiting, but CarGurus may still throttle requests

### "No price data available" error

- The vehicle/date combination might not have data in CarGurus
- Try a different date range or check if the entity ID is correct

### Network errors

- Check your internet connection
- Verify the CarGurus website is accessible

## Development

To modify or extend the scraper:

```bash
# Install development dependencies
uv sync

# Run syntax check
uv run python -m py_compile cargurus_scraper.py

# View help
uv run python cargurus_scraper.py --help
```

## License

This project is for personal use only. Respect CarGurus' terms of service and rate limits.
