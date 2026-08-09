# backend/app/evidence/transformation_log.py
"""
Every transformation (cleaning, imputation, grouping) is logged
and reversible. This addresses:
- "Preserve the original data, log transformations"
- "Make cleaning or imputation reversible"
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional, Callable
from enum import Enum
import json

class TransformationType(str, Enum):
    TYPE_CAST = "type_cast"
    MISSING_FLAG = "missing_flag"
    IMPUTATION = "imputation"
    UNIT_NORMALIZATION = "unit_normalization"
    TIMEZONE_SHIFT = "timezone_shift"
    EVENT_GROUPING = "event_grouping"
    DUPLICATE_DEDUP = "duplicate_dedup"
    LABEL_ENRICHMENT = "label_enrichment"

class TransformationRecord(BaseModel):
    """A single reversible transformation."""
    transform_id: str
    transform_type: TransformationType
    timestamp: datetime
    table: str
    row_id: int
    field: str
    original_value: Any          # BEFORE transformation
    transformed_value: Any       # AFTER transformation
    rule: str                    # Human-readable rule applied
    reversible: bool = True
    reverse_fn_name: Optional[str] = None  # Name of reversal function
    
    def reverse(self, value: Any) -> Any:
        """Reverse this transformation."""
        if not self.reversible:
            raise ValueError(f"Transformation {self.transform_id} is marked irreversible")
        return self.original_value

class TransformationLog:
    """
    Append-only log of all data transformations.
    Supports full reversibility and audit.
    """
    def __init__(self):
        self._records: list[TransformationRecord] = []
    
    def log(
        self,
        transform_type: TransformationType,
        table: str,
        row_id: int,
        field: str,
        original: Any,
        transformed: Any,
        rule: str,
        reversible: bool = True,
    ) -> TransformationRecord:
        record = TransformationRecord(
            transform_id=f"{transform_type.value}_{table}_{row_id}_{field}_{len(self._records)}",
            transform_type=transform_type,
            timestamp=datetime.utcnow(),
            table=table,
            row_id=row_id,
            field=field,
            original_value=original,
            transformed_value=transformed,
            rule=rule,
            reversible=reversible,
        )
        self._records.append(record)
        return record
    
    def reverse_all(self, table: str, row_id: int) -> dict:
        """Reverse all transformations for a given row, returning original values."""
        changes = {}
        for record in reversed(self._records):
            if record.table == table and record.row_id == row_id:
                changes[record.field] = record.original_value
        return changes
    
    def get_log(self, table: Optional[str] = None) -> list[TransformationRecord]:
        if table:
            return [r for r in self._records if r.table == table]
        return self._records
    
    def summary(self) -> dict:
        from collections import Counter
        type_counts = Counter(r.transform_type.value for r in self._records)
        return {
            "total_transformations": len(self._records),
            "by_type": dict(type_counts),
            "reversible_count": sum(1 for r in self._records if r.reversible),
            "irreversible_count": sum(1 for r in self._records if not r.reversible),
        }
    
    def export_json(self) -> str:
        """Export full log for reproducibility."""
        return json.dumps(
            [r.model_dump(mode="json") for r in self._records],
            indent=2,
            default=str,
        )

# Global transformation log — singleton
transformation_log = TransformationLog()