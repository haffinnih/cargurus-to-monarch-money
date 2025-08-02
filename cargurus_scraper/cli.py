"""Command-line interface for the CarGurus scraper."""

import argparse
import sys

from .parsers import URLParser
from .scraper import CarGurusScraper


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Extract vehicle price data from CarGurus for Monarch Money import")

    parser.add_argument("--url", help="Full CarGurus price-trends URL (alternative to --entity-id and --model-path)")
    parser.add_argument("--entity-id", help="CarGurus entity ID (e.g., 'c32015')")
    parser.add_argument("--model-path", help="URL path segment (e.g., 'Honda-Civic-Hatchbook-d2441')")
    parser.add_argument(
        "--start-date", help="Start date in YYYY-MM-DD format (defaults to earliest possible date if not provided)"
    )
    parser.add_argument("--end-date", help="End date in YYYY-MM-DD format (defaults to yesterday if not provided)")
    parser.add_argument(
        "--account-name", required=True, help="Vehicle name for Monarch CSV (e.g., '2022 Honda Civic EX-L')"
    )
    parser.add_argument("--session-cookie", required=True, help="JSESSIONID cookie value from CarGurus")

    args = parser.parse_args()

    try:
        if args.url:
            if args.entity_id or args.model_path:
                raise ValueError("Error: Cannot specify both --url and individual --entity-id/--model-path parameters")

            print("🔗 Parsing CarGurus URL...")
            model_path, entity_id = URLParser.parse_cargurus_url(args.url)
            print(f"   └── Extracted model-path: {model_path}")
            print(f"   └── Extracted entity-id: {entity_id}")
        else:
            if not args.entity_id or not args.model_path:
                raise ValueError("Error: Must provide either --url OR both --entity-id and --model-path")

            entity_id = args.entity_id
            model_path = args.model_path

        scraper = CarGurusScraper()
        filename = scraper.scrape(
            entity_id=entity_id,
            model_path=model_path,
            start_date_str=args.start_date,
            end_date_str=args.end_date,
            account_name=args.account_name,
            session_cookie=args.session_cookie,
        )

        print(f"🎉 Successfully generated CSV file: {filename}")

    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)