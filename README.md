# logslice

Fast log file parser that extracts and filters structured log entries by time range or field patterns.

## Installation

```bash
pip install logslice
```

## Usage

```python
from logslice import LogParser

parser = LogParser("app.log")

# Filter by time range
entries = parser.slice(start="2024-01-15 08:00:00", end="2024-01-15 09:00:00")

# Filter by field pattern
errors = parser.filter(level="ERROR", service="api-gateway")

# Combine filters
results = parser.slice(
    start="2024-01-15 08:00:00",
    end="2024-01-15 09:00:00"
).filter(level="ERROR")

for entry in results:
    print(entry)
```

### CLI

```bash
# Slice logs by time range
logslice app.log --start "2024-01-15 08:00:00" --end "2024-01-15 09:00:00"

# Filter by field pattern
logslice app.log --field level=ERROR --field service=api-gateway

# Output to file
logslice app.log --start "2024-01-15 08:00:00" --output filtered.log
```

## Supported Formats

- JSON structured logs
- Common log format (CLF)
- Logfmt
- Custom patterns via regex

## License

This project is licensed under the [MIT License](LICENSE).