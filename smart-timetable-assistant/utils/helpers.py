from datetime import datetime, timedelta

def parse_iso(iso_str):
    """Parse an ISO 8601 string to a datetime object, handling 'Z' suffix."""
    if not iso_str:
        return None
    try:
        # Handle 'Z' suffix if present
        clean_str = iso_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_str)
    except ValueError:
        return None

def format_datetime_friendly(iso_str):
    """Format an ISO string to a friendly format (e.g. 'Sunday, Jun 14, 10:00 AM')."""
    dt = parse_iso(iso_str)
    if not dt:
        return iso_str
    return dt.strftime("%A, %b %d, %I:%M %p")

def format_time_only(iso_str):
    """Format an ISO string to show time only (e.g. '10:00 AM')."""
    dt = parse_iso(iso_str)
    if not dt:
        return iso_str
    return dt.strftime("%I:%M %p")

def get_category_color(category):
    """Return background and border color classes/hex for a category."""
    colors = {
        'Work': {
            'bg': 'rgba(138, 43, 226, 0.15)',      # Purple
            'border': '#8A2BE2',
            'text': '#E9D5FF'
        },
        'Study': {
            'bg': 'rgba(59, 130, 246, 0.15)',      # Blue
            'border': '#3B82F6',
            'text': '#DBEAFE'
        },
        'Personal': {
            'bg': 'rgba(16, 185, 129, 0.15)',     # Green
            'border': '#10B981',
            'text': '#D1FAE5'
        },
        'Meeting': {
            'bg': 'rgba(245, 158, 11, 0.15)',     # Amber
            'border': '#F59E0B',
            'text': '#FEF3C7'
        },
        'Exercise': {
            'bg': 'rgba(239, 68, 68, 0.15)',      # Red
            'border': '#EF4444',
            'text': '#FEE2E2'
        }
    }
    return colors.get(category.title() if category else 'Other', {
        'bg': 'rgba(107, 114, 128, 0.15)',         # Gray / Other
        'border': '#6B7280',
        'text': '#F3F4F6'
    })

def get_duration_minutes(start_iso, end_iso):
    """Get the duration of an event in minutes."""
    start = parse_iso(start_iso)
    end = parse_iso(end_iso)
    if not start or not end:
        return 0
    delta = end - start
    return int(delta.total_seconds() / 60)

def get_week_range(date_obj=None):
    """Get the start (Monday) and end (Sunday) dates of the current week."""
    if date_obj is None:
        date_obj = datetime.now()
    start_of_week = date_obj - timedelta(days=date_obj.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week.date(), end_of_week.date()
