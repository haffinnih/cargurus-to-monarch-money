# CarGurus to Monarch Money Vehicle Value Scraper

A Python package that extracts daily vehicle price data from [CarGurus](https://www.cargurus.com/) API and formats it for import into [Monarch Money](https://www.monarchmoney.com/)'s vehicle tracking system.

I've been wanting to create this for months(? probably over a year at this point). It was a relatively simple mini-project, but I just hadn't made the time to complete it.

I took a stab at it tonight with [Claude](https://claude.ai).

- Initial planning with Claude on web + poking around on Car Gurus site to discover API (~25 mins)
- Initial commit to functional MVP with [Claude Code](https://www.anthropic.com/claude-code) (~10 mins)
- Further refinement with user-friendly adaptions and improvements (~30 mins)
- Updating README manually and figuring out how to capture a Claude conversation because I don't trust link sharing to not decay at some point in the future (~30 mins)
  - I had to install Chrome to use [Claude Share](https://chromewebstore.google.com/detail/claude-share/khnkcffkddpblpjfefjalndfpgbbjfpc) to get a mostly working markdown export. It needed some love, but we got there!

Enjoy! 🫡

## Features

- 📊 Extracts historical vehicle price data from CarGurus
- 💰 Outputs CSV files compatible with Monarch Money import format
- 📅 Handles date range chunking automatically for granular data
- 🔄 Forward-fills missing data points to maintain continuity
- ✅ Comprehensive input validation and error handling
- ⏱️ Rate limiting to respect API constraints
- 🔗 URL parsing for easy parameter extraction

## Installation & Usage

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. Make sure you have uv installed.

### Quick Start

```bash
# Clone the repository
git clone https://github.com/haffinnih/cargurus-to-monarch-money.git
cd cargurus-to-monarch-money

# Run the scraper
uv run cargurus-scraper --help
```

### Basic Command

```bash
# Using URL (easiest method - just copy from your browser!)
uv run cargurus-scraper \
  --url "https://www.cargurus.com/research/price-trends/Honda-Civic-Hatchback-d2441?entityIds=c32015&startDate=1740805200000&endDate=1754193599999" \
  --account-name "2022 Honda Civic EX-L" \
  --session-cookie "ABC123XYZ456"

# Or with individual parameters and specific dates
uv run cargurus-scraper \
  --entity-id "c32015" \
  --model-path "Honda-Civic-Hatchback-d2441" \
  --start-date "2024-01-01" \
  --end-date "2024-06-30" \
  --account-name "2022 Honda Civic EX-L" \
  --session-cookie "ABC123XYZ456"

# Using URL with custom date range
uv run cargurus-scraper \
  --url "https://www.cargurus.com/research/price-trends/Honda-Civic-Hatchback-d2441?entityIds=c32015" \
  --start-date "2024-01-01" \
  --end-date "2024-06-30" \
  --account-name "2022 Honda Civic EX-L" \
  --session-cookie "ABC123XYZ456"
```

### Parameters

| Parameter          | Description                                                        | Example                       |
| ------------------ | ------------------------------------------------------------------ | ----------------------------- |
| `--url`            | Full CarGurus price-trends URL (alternative to entity-id/model-path) | See examples above            |
| `--entity-id`      | CarGurus vehicle entity ID (required if not using --url)          | `c32015`                      |
| `--model-path`     | URL path segment from CarGurus (required if not using --url)      | `Honda-Civic-Hatchback-d2441` |
| `--start-date`     | Start date in YYYY-MM-DD format (optional, defaults to 1 year ago) | `2025-01-01`                  |
| `--end-date`       | End date in YYYY-MM-DD format (optional, defaults to yesterday)    | `2025-12-31`                  |
| `--account-name`   | Vehicle name for CSV output                                        | `2022 Honda Civic EX-L`       |
| `--session-cookie` | JSESSIONID cookie from CarGurus                                    | `ABC123XYZ456`                |

### Getting Required Parameters

#### Method 1: Using URL (Recommended)

1. Go to [CarGurus Price Trends](https://www.cargurus.com/research/price-trends)
2. Navigate to your desired make/model/year
3. Uncheck all charts except the one you want to fetch
4. Copy the entire URL from your browser - it will look like:
   ```
   https://www.cargurus.com/research/price-trends/Honda-Civic-Hatchback-d2441?entityIds=c32015&startDate=1740805200000&endDate=1754107199999
   ```
5. Use this URL directly with the `--url` parameter

#### Method 2: Manual Parameter Extraction

If you prefer to extract the parameters manually:
1. From the URL above, note:
   - Model path: `Honda-Civic-Hatchback-d2441` (from the URL path)
   - Entity ID: `c32015` (from the `entityIds` parameter)
2. Use these with `--entity-id` and `--model-path` parameters

#### Getting Session Cookie

1. Open browser developer tools (F12)
2. Go to Application/Storage tab → Cookies → cargurus.com
3. Find the `JSESSIONID` cookie value
4. Copy the value (without "JSESSIONID=")

## Output

The script generates CSV files in an `output/` directory with the following format:

```csv
Date,Balance,Account
2024-01-01,24988.09,2022 <account-name>
2024-01-02,24988.09,2022 <account-name>
2024-01-03,24979.12,2022 <account-name>
```

**File location:** `output/{account_name_sanitized}_{start_date}_{end_date}.csv`

Example: `output/2022_Honda_Civic_EX-L_2024-01-01_2024-06-30.csv`

The `output/` directory is automatically created if it doesn't exist and is ignored by git to prevent committing your personal vehicle data.

**Note:** When dates are not specified:

- **Start date** defaults to 1 year ago (the earliest data available from CarGurus)
- **End date** defaults to yesterday (since CarGurus typically doesn't have same-day price data available)

This means running the script with no date parameters will give you a full year of historical price data.

## Import to Monarch Money

1. Log into Monarch Money
2. Go the account you want to edit
3. Download the balance history ([help](https://help.monarchmoney.com/hc/en-us/articles/15526600975764-Downloading-Transaction-or-Account-History))
4. Edit it with the data you got from the csv output
5. Upload the CSV back to your account ([help](https://help.monarchmoney.com/hc/en-us/articles/14882425704212-Upload-Account-Balance-History))

## Error Handling

The script provides clear error messages for common issues:

- **Invalid date format:** "Error: Date must be in YYYY-MM-DD format"
- **Start date too old:** "Error: Start date cannot be more than 1 year ago"
- **End date in future:** "Error: End date cannot be in the future"
- **Missing parameters:** "Error: Missing required parameter: entity_id"
- **Invalid session:** "Error: Invalid session cookie. Please provide a valid JSESSIONID"
- **No data found:** "Error: No price data available for the specified vehicle and date range"

## Limitations

- Start date cannot be more than 1 year ago (CarGurus API limitation)
- Requires valid JSESSIONID cookie from an active CarGurus session
- Rate limited to prevent overwhelming the API
- Data availability depends on CarGurus having price information for your vehicle

## Examples

### Toyota Corolla (using URL method)

```bash
uv run cargurus-scraper \
  --url "https://www.cargurus.com/research/price-trends/Toyota-Corolla-d295?entityIds=c26003" \
  --account-name "2017 Toyota Corolla" \
  --session-cookie "your_session_cookie_here"
```

## Troubleshooting

### "Invalid session cookie" error

- Your JSESSIONID cookie has expired
- Get a fresh cookie by navigating around CarGurus again

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

# View help
uv run cargurus-scraper --help

# Run the package directly (alternative to console script)
uv run python -m cargurus_scraper.cli --help
```

## License

This project is for personal use only. Respect CarGurus' terms of service and rate limits.

[MIT License](LICENSE)