# Logs Directory

This directory contains log files for brand processing runs.

## Log File Types

### 1. Daily Logs (`batch_YYYYMMDD.log`)
Human-readable logs aggregated by day. All batch runs on the same day are logged to the same file.

**Format:**
```
[timestamp] [run_id] [EVENT] brand_name | details
```

**Example:**
```
[2025-02-16 14:30:25] [20250216_143025_001_digikala] [START   ] دیجی‌کالا | website=https://www.digikala.com
[2025-02-16 14:30:47] [20250216_143025_001_digikala] [SUCCESS ] دیجی‌کالا | duration=22.34s | outputs=4
```

### 2. Structured Logs (`run_YYYYMMDD_HHMMSS.jsonl`)
Machine-readable JSON Lines format. One file per batch run.

**Format:** Each line is a complete JSON object
```json
{
  "timestamp": "2025-02-16T14:30:25.123456",
  "run_id": "20250216_143025_001_digikala",
  "event": "START|SKIP|SUCCESS|FAIL",
  "brand_name": "دیجی‌کالا",
  "details": "...",
  "duration_seconds": 22.34
}
```

## Events

| Event | Description |
|-------|-------------|
| `START` | Brand processing started |
| `SKIP` | Brand skipped (unchanged since last run) |
| `SUCCESS` | Brand processed successfully |
| `FAIL` | Brand processing failed |

## Run ID Format

```
{batch_timestamp}_{index}_{sanitized_brand_name}
```

Example: `20250216_143025_001_digikala`

- `20250216_143025`: Batch start timestamp (YYYYMMDD_HHMMSS)
- `001`: Brand index in batch (3 digits)
- `digikala`: Sanitized brand name (lowercase, alphanumeric + hyphens)

## Usage

**View today's logs:**
```bash
tail -f logs/batch_$(date +%Y%m%d).log
```

**Query structured logs:**
```bash
# Count successful runs
grep SUCCESS logs/run_*.jsonl | wc -l

# Extract all failures with jq
cat logs/run_*.jsonl | jq 'select(.event == "FAIL")'

# Calculate average duration
cat logs/run_*.jsonl | jq 'select(.duration_seconds) | .duration_seconds' | awk '{sum+=$1; count++} END {print sum/count}'
```

## Retention

- Daily logs: Keep for 30 days (manual cleanup recommended)
- Structured logs: Keep for 90 days (for analytics)
- No automatic rotation - implement log rotation if needed
