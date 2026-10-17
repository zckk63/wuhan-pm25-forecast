import csv
import hashlib
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
MANIFEST_PATH = RAW_DIR / "source_manifest_2025.csv"
START_DATE = date(2025, 1, 1)
DAY_COUNT = 365


def valid_csv(payload):
    header = payload[:8192].lstrip(b"\xef\xbb\xbf")
    return (
        len(payload) > 1000
        and b"date,hour,type" in header
        and b"\xe6\xad\xa6\xe6\xb1\x89" in header
    )


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    failures = []

    for index in range(DAY_COUNT):
        day = START_DATE + timedelta(days=index)
        date_text = day.strftime("%Y%m%d")
        filename = f"china_cities_{date_text}.csv"
        output_path = RAW_DIR / filename
        url = f"https://quotsoft.net/air/data/{filename}"

        payload = None
        status = "cached"
        fetched_at = ""

        if output_path.exists():
            existing = output_path.read_bytes()
            if valid_csv(existing):
                payload = existing
            else:
                output_path.unlink()

        if payload is None:
            status = "downloaded"
            error_message = ""
            for attempt in range(1, 4):
                try:
                    request = Request(
                        url,
                        headers={"User-Agent": "WuhanPM25CourseProject/1.0"},
                    )
                    with urlopen(request, timeout=40) as response:
                        payload = response.read()

                    if not valid_csv(payload):
                        raise ValueError("Response is not the expected Wuhan city CSV")

                    temporary_path = output_path.with_suffix(".csv.part")
                    temporary_path.write_bytes(payload)
                    temporary_path.replace(output_path)
                    fetched_at = datetime.now(UTC).isoformat()
                    break
                except (OSError, ValueError) as error:
                    error_message = str(error)
                    if attempt < 3:
                        time.sleep(attempt * 2)

            if payload is None:
                failures.append(date_text)
                manifest_rows.append(
                    {
                        "date": date_text,
                        "url": url,
                        "status": "failed",
                        "bytes": 0,
                        "sha256": "",
                        "fetched_at_utc": "",
                        "error": error_message,
                    }
                )
                print(f"FAILED {date_text}: {error_message}", flush=True)
                continue

        manifest_rows.append(
            {
                "date": date_text,
                "url": url,
                "status": status,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "fetched_at_utc": fetched_at,
                "error": "",
            }
        )

        if (index + 1) % 25 == 0 or index + 1 == DAY_COUNT:
            print(
                f"Checked {index + 1}/{DAY_COUNT} days; "
                f"download failures so far: {len(failures)}",
                flush=True,
            )

        if status == "downloaded":
            time.sleep(1)

    with MANIFEST_PATH.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "date",
                "url",
                "status",
                "bytes",
                "sha256",
                "fetched_at_utc",
                "error",
            ],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"CSV files present: {sum(row['status'] != 'failed' for row in manifest_rows)}")
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"Failed dates: {failures}")


if __name__ == "__main__":
    main()
