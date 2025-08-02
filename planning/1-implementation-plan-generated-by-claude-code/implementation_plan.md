# CarGurus Vehicle Value Scraper Implementation Plan

## Overview
Build a Python script that scrapes daily vehicle price data from CarGurus API and outputs CSV files compatible with Monarch Money's import format.

## Implementation Steps

### 1. Project Structure Setup
- Create `cargurus_scraper.py` as the main script
- Create `pyproject.toml` for uv package management
- Create `implementation_plan.md` to document this plan ✓
- Optional: Add `README.md` with usage instructions

### 2. Core Dependencies (managed with uv)
- `requests` - HTTP client for API calls
- `argparse` - Command line argument parsing (built-in)
- `datetime` - Date manipulation and validation (built-in)
- `csv` - CSV file generation (built-in)
- `time` - Rate limiting between API calls (built-in)

### 3. Main Components

#### Input Validation Module
- Validate date format (YYYY-MM-DD)
- Ensure start date is within 1 year
- Ensure start date < end date
- Validate required parameters

#### Date Processing Module
- Convert YYYY-MM-DD to Unix milliseconds
- Generate monthly chunks for API calls
- Handle date range iteration

#### API Client Module
- Make requests to CarGurus price-trends endpoint
- Handle authentication with JSESSIONID cookie
- Implement error handling for HTTP failures
- Add rate limiting between requests

#### Data Processing Module
- Extract price points from API response
- Convert Unix timestamps back to YYYY-MM-DD
- Implement forward-fill for missing data gaps
- Round prices to 2 decimal places

#### CSV Export Module
- Generate Monarch Money compatible CSV format
- Sanitize account names for filenames
- Create proper headers: Date, Balance, Account

### 4. Error Handling
- Input validation errors with specific messages
- API authentication and network errors
- Missing data scenarios
- Malformed response handling

### 5. Command Line Interface
Accept parameters: `--entity-id`, `--model-path`, `--start-date`, `--end-date`, `--account-name`, `--session-cookie`

## Key Technical Decisions
- Use Python with uv for modern package management
- Monthly chunking strategy to get granular daily data
- Forward-fill missing dates to maintain continuity
- Robust error handling with user-friendly messages
- File naming: `{sanitized_account}_{start_date}_{end_date}.csv`

The script will be self-contained and ready to run with `uv run cargurus_scraper.py`.