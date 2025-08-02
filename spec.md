# CarGurus to Monarch Money Vehicle Value Scraper

## Project Overview
A script that extracts daily vehicle price data from CarGurus API and formats it for import into Monarch Money's vehicle tracking system.

## Core Functionality
Extract historical vehicle price data from CarGurus and output it as a CSV file compatible with Monarch Money's import format.

## Input Parameters
The script should accept the following inputs (command line arguments or prompts):

1. **CarGurus Entity ID** (string): The specific vehicle entity ID (e.g., "c32015" for 2022 Honda Civic Hatchback)
2. **Model Path Segment** (string): The URL path segment (e.g., "Honda-Civic-Hatchback-d2441")  
3. **Start Date** (string): Human-readable date in YYYY-MM-DD format (e.g., "2024-01-01")
4. **End Date** (string): Human-readable date in YYYY-MM-DD format (e.g., "2024-12-31")
5. **Account Name** (string): The vehicle name for Monarch CSV (e.g., "2022 Honda Civic EX-L")
6. **JSESSIONID Cookie** (string): Session cookie value from CarGurus (user must provide manually)

## API Details

**Endpoint:** `GET https://www.cargurus.com/research/price-trends/{modelPath}`

**Required Query Parameters:**
- `entityIds`: The entity ID (e.g., "c32015")
- `startDate`: Unix timestamp in milliseconds 
- `endDate`: Unix timestamp in milliseconds
- `_data`: Always set to `routes/($intl).research.price-trends.$makeModelSlug`

**Required Headers:**
- `Cookie: JSESSIONID={cookie_value}`

**Response Structure:**
The API returns JSON with price data in `pricePointsEntities[0].pricePoints[]` array:
```json
{
  "pricePointsEntities": [
    {
      "entityId": "c32015",
      "label": "2022 Civic Hatchback", 
      "pricePoints": [
        {
          "date": 1751256000000,
          "price": 24988.09293193717
        }
      ]
    }
  ]
}
```

## Data Processing Logic

### Date Range Handling
1. **Validation**: Ensure start date is not more than 1 year ago from current date
2. **Validation**: Ensure start date < end date
3. **Chunking**: Break the date range into monthly segments to get granular daily data
4. **API Calls**: Make separate API calls for each monthly chunk

### Data Extraction
1. Extract price points from `pricePointsEntities[0].pricePoints` array
2. Convert Unix timestamps (milliseconds) to YYYY-MM-DD format
3. Round prices to 2 decimal places

### Gap Filling
1. **Forward Fill**: If there are gaps between dates, fill with the last known price
2. **Missing Data**: If an entire month returns no data, forward-fill from the previous known value
3. **No Data Error**: If no price data exists at all, exit with error message

## Output Format

Generate a CSV file with Monarch Money's expected format:

```csv
Date,Balance,Account
2024-01-01,24988.09,2022 Honda Civic EX-L
2024-01-02,24988.09,2022 Honda Civic EX-L
2024-01-03,24979.12,2022 Honda Civic EX-L
```

**File Naming:** `{account_name_sanitized}_{start_date}_{end_date}.csv`

## Error Handling

### Input Validation Errors
- Invalid date format → "Error: Date must be in YYYY-MM-DD format"
- Start date > 1 year ago → "Error: Start date cannot be more than 1 year ago"
- Start date >= end date → "Error: Start date must be before end date"
- Missing required parameters → "Error: Missing required parameter: {param_name}"

### API Errors
- Network/HTTP errors → "Error: Failed to fetch data from CarGurus: {error_details}"
- Invalid session cookie → "Error: Invalid session cookie. Please provide a valid JSESSIONID"
- Rate limiting → "Error: Rate limited by CarGurus. Please try again later"

### Data Errors
- No price data found → "Error: No price data available for the specified vehicle and date range"
- Malformed API response → "Error: Unexpected response format from CarGurus API"

## Technical Requirements

### Dependencies
- HTTP client for API requests
- Date manipulation library
- CSV writing capability
- Command line argument parsing

### Date Conversion
- Input: Human-readable YYYY-MM-DD
- API: Unix timestamps in milliseconds  
- Output: YYYY-MM-DD format

### Monthly Chunking Strategy
For a date range like 2024-01-01 to 2024-06-30:
- Chunk 1: 2024-01-01 to 2024-01-31
- Chunk 2: 2024-02-01 to 2024-02-29  
- Chunk 3: 2024-03-01 to 2024-03-31
- etc.

Each chunk gets converted to Unix milliseconds for the API call.

## Example Usage

```bash
# Command line example
python cargurus_scraper.py \
  --entity-id "c32015" \
  --model-path "Honda-Civic-Hatchback-d2441" \
  --start-date "2024-01-01" \
  --end-date "2024-06-30" \
  --account-name "2022 Honda Civic EX-L" \
  --session-cookie "ABC123XYZ"
```

## Success Criteria
1. Successfully extracts daily price data from CarGurus API
2. Handles monthly chunking automatically
3. Fills data gaps appropriately  
4. Outputs valid CSV compatible with Monarch Money
5. Provides clear error messages for common failure scenarios
6. Validates all inputs before processing

## Notes for Implementation
- The `_data` parameter appears to be a route identifier and should always be set to `routes/($intl).research.price-trends.$makeModelSlug`
- CarGurus timestamps are in milliseconds, not seconds
- Price values may have many decimal places but should be rounded to 2 for financial data
- The user is responsible for obtaining a valid JSESSIONID cookie from their browser