# app/timeline/schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional, Any

class EventCategory(str, Enum):
    ADMISSION = "admission"
    DISCHARGE = "discharge"
    TRANSFER = "transfer"
    ICU_ADMISSION = "icu_admission"
    ICU_DISCHARGE = "icu_discharge"
    LAB_RESULT = "lab_result"
    MEDICATION = "medication"
    DIAGNOSIS = "diagnosis"
    PROCEDURE = "procedure"
    ICU_OBSERVATION = "icu_observation"
    ICU_OUTPUT = "icu_output"

class SourceTrace(BaseModel):
    collection: str = Field(..., description="MongoDB collection name")
    fields: str = Field(..., description="Fields used from document")
    doc_id: str = Field(..., description="MongoDB _id or business key")
    charttime: Optional[datetime] = Field(None)
    
    def to_dict(self) -> dict:
        return {
            "collection": self.collection,
            "fields": self.fields,
            "doc_id": self.doc_id,
            "charttime": self.charttime.isoformat() if self.charttime else None,
        }

class TimelineEvent(BaseModel):
    event_id: str
    category: EventCategory
    timestamp: datetime
    end_timestamp: Optional[datetime] = None
    label: str
    detail: dict = Field(default_factory=dict)
    source: SourceTrace
    is_abnormal: bool = False
    uncertainty: Optional[str] = None

class EventGroup(BaseModel):
    group_id: str
    category: EventCategory
    start_time: datetime
    end_time: datetime
    event_count: int
    summary_stats: dict = Field(default_factory=dict)
    representative_events: list[TimelineEvent] = Field(default_factory=list)
    is_collapsed: bool = True
    member_source_traces: list[SourceTrace] = Field(default_factory=list)

class PatientTimeline(BaseModel):
    subject_id: int
    hadm_id: int
    admission_time: datetime
    discharge_time: Optional[datetime] = None
    events: list[TimelineEvent] = Field(default_factory=list)
    groups: list[EventGroup] = Field(default_factory=list)
    quality_report: dict = Field(default_factory=dict)