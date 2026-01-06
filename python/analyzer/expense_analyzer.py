import argparse
import csv
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple


REQUIRED_HEADERS = {"date", "category", "amount"}


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse YYYY-MM-DD date strings. Returns None if invalid."""
    date_str = (date_str or "").strip()
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def parse_amount(amount_str: str) -> Optional[float]:
    """
    Convert amount strings to float safely.
    Handles values like '12.50', '£12.50', '  12.50  '.
    Returns None if invalid.
    """
    s = (amount_str or "").strip()
    if not s:
        return None

    # Remove currency symbols and commas (e.g., £1,200.50)
    s = re.sub(r"[£$,]", "", s)

    try:
        return float(s)
    except ValueError:
        return None


def validate_headers(fieldnames) -> Tuple[bool, str]:
    if not fieldnames:
        return False, "CSV file appears to be empty or missing headers."

    headers = {h.strip().lower() for h in fieldnames if h}
    missing = REQUIRED_HEADERS - headers
    if missing:
        return False, f"Missing required CSV headers: {', '.join(sorted(missing))}. Expected: date,category,amount"
    return True, ""


def analyze_expenses(
    file_path: Path,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> Tuple[Dict[str, float], int, int]:
    """
    Returns:
      totals: dict of category -> total spend
      processed_rows: number of rows processed (valid or invalid)
      skipped_rows: number of rows skipped due to invalid data or filtering
    """
    totals = defaultdict(float)
    processed_rows = 0
    skipped_rows = 0

    with file_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        ok, msg = validate_headers(reader.fieldnames)
        if not ok:
            raise ValueError(msg)

        for row in reader:
            processed_rows += 1

            category = (row.get("category") or "").strip()
            amount = parse_amount(row.get("amount"))
            date_val = parse_date(row.get("date"))

            # Basic validation
            if not category or amount is None:
                skipped_rows += 1
                continue

            # Optional date filtering (only if date column is valid)
            if date_from or date_to:
                if date_val is None:
                    skipped_rows += 1
                    continue

                if date_from and date_val < date_from:
                    skipped_rows += 1
                    continue
                if date_to and date_val > date_to:
                    skipped_rows += 1
                    continue

            totals[category] += amount

    return dict(totals), processed_rows, skipped_rows


def print_summary(totals: Dict[str, float]) -> None:
    if not totals:
        print("\nNo expenses found for the given file/filter.\n")
        return

    total_spent = sum(totals.values())
    print("\nExpense Summary")
    print("-" * 40)
    print(f"Total spent: {total_spent:.2f}\n")

    # Sort highest spend first
    for category, amount in sorted(totals.items(), key=lambda x: x[1], reverse=True):
        pct = (amount / total_spent) * 100 if total_spent else 0
        print(f"{category:<20} {amount:>10.2f}   ({pct:>5.1f}%)")

    print("-" * 40)


def export_summary_csv(totals: Dict[str, float], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    total_spent = sum(totals.values())
    rows = sorted(totals.items(), key=lambda x: x[1], reverse=True)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["category", "amount", "percent_of_total"])
        for category, amount in rows:
            pct = (amount / total_spent) * 100 if total_spent else 0
            writer.writerow([category, f"{amount:.2f}", f"{pct:.1f}"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze expenses from a CSV file and summarize spending by category."
    )
    parser.add_argument("file", help="Path to the expenses CSV file")
    parser.add_argument("--from", dest="date_from", help="Start date (YYYY-MM-DD)", default=None)
    parser.add_argument("--to", dest="date_to", help="End date (YYYY-MM-DD)", default=None)
    parser.add_argument("--export", help="Export summary to a CSV file (e.g., summary.csv)", default=None)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    file_path = Path(args.file).expanduser().resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    date_from = parse_date(args.date_from) if args.date_from else None
    date_to = parse_date(args.date_to) if args.date_to else None

    if args.date_from and date_from is None:
        raise ValueError("Invalid --from date format. Use YYYY-MM-DD.")
    if args.date_to and date_to is None:
        raise ValueError("Invalid --to date format. Use YYYY-MM-DD.")
    if date_from and date_to and date_from > date_to:
        raise ValueError("--from date cannot be after --to date.")

    totals, processed, skipped = analyze_expenses(file_path, date_from, date_to)
    print_summary(totals)
    print(f"Rows processed: {processed} | Rows skipped: {skipped}\n")

    if args.export:
        out_path = Path(args.export).expanduser().resolve()
        export_summary_csv(totals, out_path)
        print(f"Exported summary to: {out_path}\n")


if __name__ == "__main__":
    main()
