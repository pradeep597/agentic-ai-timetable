from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class EventBase(BaseModel):
    title: str = Field(..., description="The title or name of the event/meeting")
    description: Optional[str] = Field(None, description="Detailed description or notes about the event")
    start_time: str = Field(..., description="Start time in ISO format (YYYY-MM-DDTHH:MM:SS)")
    end_time: str = Field(..., description="End time in ISO format (YYYY-MM-DDTHH:MM:SS)")
    category: str = Field("Other", description="Category of event (e.g. Work, Study, Personal, Meeting, Exercise)")
    reminder_time: Optional[str] = Field(None, description="Optional reminder trigger time in ISO format")

    @field_validator('start_time', 'end_time', 'reminder_time')
    @classmethod
    def validate_iso_format(cls, v):
        if v is None:
            return v
        try:
            # Check if it parses correctly
            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except ValueError:
            raise ValueError("Time must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)")

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, description="New title of the event")
    description: Optional[str] = Field(None, description="New description or notes")
    start_time: Optional[str] = Field(None, description="New start time in ISO format")
    end_time: Optional[str] = Field(None, description="New end time in ISO format")
    category: Optional[str] = Field(None, description="New category")
    google_event_id: Optional[str] = Field(None, description="Associated Google Calendar Event ID")
    reminder_time: Optional[str] = Field(None, description="New reminder time")

class EventResponse(EventBase):
    id: int
    google_event_id: Optional[str] = None
    reminder_sent: int = 0
    created_at: str
