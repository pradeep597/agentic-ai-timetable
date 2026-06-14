import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import db
from utils import helpers

def check_pending_reminders(minutes_ahead=30):
    """
    Find events starting within the next `minutes_ahead` minutes 
    that have not had reminders sent yet.
    """
    now = datetime.now()
    cutoff = now + timedelta(minutes=minutes_ahead)
    
    events = db.get_events(
        start_date=now.strftime("%Y-%m-%d"),
        end_date=cutoff.strftime("%Y-%m-%d")
    )
    
    pending = []
    for event in events:
        if event['reminder_sent'] == 1:
            continue
            
        start_dt = helpers.parse_iso(event['start_time'])
        if not start_dt:
            continue
            
        # Check if the event starts in the future and within the threshold
        if now <= start_dt <= cutoff:
            pending.append(event)
            
    return pending

def send_reminder(event_id):
    """
    Simulate sending a reminder for the given event.
    Updates database status to reminder_sent = 1.
    """
    conn = db.get_db_connection()
    event = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    conn.close()
    
    if not event:
        return False, "Event not found"
        
    event = dict(event)
    
    # Mark as sent
    db.update_event(event_id, reminder_sent=1)
    
    # Build beautiful notification payload
    time_str = helpers.format_time_only(event['start_time'])
    msg = f"🔔 Reminder: '{event['title']}' is starting soon at {time_str}!"
    
    # In a real app, this would use Twilio or SMTP. Here we simulate it.
    print(f"MOCK REMINDER SENT: {msg}")
    
    return True, msg
