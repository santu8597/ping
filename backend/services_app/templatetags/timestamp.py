from django import template

from datetime import datetime, timezone, timedelta


register = template.Library()

def unit_to_timestamp(value):
    try:
        # Define IST (UTC +5:30)
        ist = timezone(timedelta(hours=5, minutes=30))

        # Check if ISO 8601 string
        if isinstance(value, str) and "T" in value and "Z" in value:
            # Convert to UTC-aware datetime
            timestamp = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(ist)
        else:
            # Assume Unix timestamp (UTC), convert and localize to IST
            timestamp = datetime.utcfromtimestamp(int(value)).replace(tzinfo=timezone.utc).astimezone(ist)

        # Format: Apr 10, 2025, 4:50:28 PM
        return timestamp.strftime("%b %d, %Y, %I:%M:%S %p")
    except (ValueError, TypeError):
        return "Invalid timestamp"

# Register the filter
register.filter("timestamp", unit_to_timestamp)
