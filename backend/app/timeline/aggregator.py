
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict
import statistics

from app.timeline.schemas import (
    TimelineEvent, EventCategory, EventGroup, SourceTrace
)
from app.config import get_settings

settings = get_settings()


class EventAggregator:
    """
    Aggregates high-volume events into collapsible groups.
    
    Design principles:
    - NEVER hide abnormal events
    - NEVER hide uncertainty
    - ALWAYS preserve all source traces
    - Groups are reversible — you can always expand to see all events
    """
    
    # Categories that are typically high-volume
    HIGH_VOLUME_CATEGORIES = {
        EventCategory.ICU_OBSERVATION,
        EventCategory.ICU_OUTPUT,
    }
    
    # Time windows for aggregation
    TIME_WINDOWS = {
        "1min": timedelta(minutes=1),
        "5min": timedelta(minutes=5),
        "15min": timedelta(minutes=15),
        "1hr": timedelta(hours=1),
        "4hr": timedelta(hours=4),
        "1day": timedelta(days=1),
    }
    
    def __init__(
        self,
        high_volume_threshold: int = None,
        default_time_window: str = "1hr",
    ):
        self.threshold = high_volume_threshold or settings.HIGH_VOLUME_THRESHOLD
        self.time_window = self.TIME_WINDOWS.get(
            default_time_window, timedelta(hours=1)
        )
    
    def aggregate(
        self, events: list[TimelineEvent]
    ) -> tuple[list[TimelineEvent], list[EventGroup]]:
        """
        Main entry point: separate low-volume events from
        high-volume groups.
        
        Returns (ungrouped_events, groups).
        """
        # Separate high-volume and low-volume
        high_volume = []
        low_volume = []
        
        for event in events:
            if event.category in self.HIGH_VOLUME_CATEGORIES:
                high_volume.append(event)
            else:
                low_volume.append(event)
        
        # Group high-volume events by (category, itemid)
        key_to_events = defaultdict(list)
        for event in high_volume:
            key = f"{event.category.value}_{event.detail.get('itemid', 'na')}"
            key_to_events[key].append(event)
        
        # Create groups or keep as individual events
        groups = []
        still_ungrouped = []
        
        for key, evts in key_to_events.items():
            if len(evts) < self.threshold:
                # Not enough events to warrant grouping
                still_ungrouped.extend(evts)
            else:
                # Create one or more groups
                event_groups = self._create_groups(key, evts)
                groups.extend(event_groups)
        
        # Combine low-volume + sub-threshold events
        all_ungrouped = low_volume + still_ungrouped
        all_ungrouped.sort(key=lambda e: (e.timestamp, e.category.value))
        groups.sort(key=lambda g: g.start_time)
        
        return all_ungrouped, groups
    
    def _create_groups(
        self, key: str, events: list[TimelineEvent]
    ) -> list[EventGroup]:
        """
        Create groups for a stream of events.
        
        Strategy:
        - Try time-windowed grouping first
        - If events span > 24 hours, create multiple groups
        - Otherwise, create one group with all events
        """
        if not events:
            return []
        
        # Check time span
        first_time = events[0].timestamp
        last_time = events[-1].timestamp
        total_span = last_time - first_time
        
        # If span > 24 hours, create time-windowed groups
        if total_span > timedelta(hours=24):
            return self._time_windowed_groups(key, events)
        
        # Otherwise, single group
        group = self._create_single_group(key, events)
        return [group] if group else []
    
    def _create_single_group(
        self, key: str, events: list[TimelineEvent]
    ) -> Optional[EventGroup]:
        """Create a single EventGroup from a list of events."""
        if not events:
            return None
        
        # Compute summary statistics
        numeric_values = []
        for e in events:
            val = e.detail.get("value")
            if isinstance(val, (int, float)):
                numeric_values.append(val)
        
        summary = {}
        if numeric_values:
            summary = {
                "count": len(numeric_values),
                "mean": round(statistics.mean(numeric_values), 2),
                "min": round(min(numeric_values), 2),
                "max": round(max(numeric_values), 2),
                "median": round(statistics.median(numeric_values), 2),
            }
            if len(numeric_values) > 1:
                summary["sd"] = round(statistics.stdev(numeric_values), 2)
                summary["iqr"] = round(
                    self._iqr(numeric_values), 2
                )
        
        # Count abnormal and uncertain events
        abnormal_count = sum(1 for e in events if e.is_abnormal)
        uncertain_count = sum(1 for e in events if e.uncertainty)
        
        # Select representative events
        representative = self._select_representative(events)
        
        # Preserve ALL source traces
        all_traces = [e.source for e in events]
        
        return EventGroup(
            group_id=f"group_{key}_{first_time.isoformat()}",
            category=events[0].category,
            start_time=events[0].timestamp,
            end_time=events[-1].timestamp,
            event_count=len(events),
            summary_stats={
                **summary,
                "abnormal_count": abnormal_count,
                "uncertain_count": uncertain_count,
                "abnormal_pct": round(abnormal_count / len(events) * 100, 1),
            },
            representative_events=representative,
            is_collapsed=True,
            member_source_traces=all_traces,
        )
    
    def _time_windowed_groups(
        self, key: str, events: list[TimelineEvent]
    ) -> list[EventGroup]:
        """
        Create multiple groups using time windows.
        Each window becomes a separate EventGroup.
        """
        groups = []
        window_start = events[0].timestamp
        window_events = []
        
        for event in events:
            # Check if event falls within current window
            if event.timestamp <= window_start + self.time_window:
                window_events.append(event)
            else:
                # Close current window
                if window_events:
                    group = self._create_single_group(key, window_events)
                    if group:
                        groups.append(group)
                
                # Start new window
                window_start = event.timestamp
                window_events = [event]
        
        # Close last window
        if window_events:
            group = self._create_single_group(key, window_events)
            if group:
                groups.append(group)
        
        return groups
    
    def _select_representative(
        self, events: list[TimelineEvent]
    ) -> list[TimelineEvent]:
        """
        Select representative events to show in a collapsed group.
        
        Always keep:
        1. First event
        2. Last event
        3. ALL abnormal events (never hide these)
        4. Events with uncertainty (show data quality issues)
        5. Min/max value events (show range extremes)
        """
        if len(events) <= 3:
            return events
        
        representative = []
        seen_ids = set()
        
        def add_if_new(evt: TimelineEvent):
            if evt.event_id not in seen_ids:
                representative.append(evt)
                seen_ids.add(evt.event_id)
        
        # 1. First event
        add_if_new(events[0])
        
        # 2. All abnormal events — NEVER hide
        for e in events:
            if e.is_abnormal:
                add_if_new(e)
        
        # 3. Events with uncertainty
        for e in events:
            if e.uncertainty:
                add_if_new(e)
        
        # 4. Min and max value events
        numeric_events = [
            (e, e.detail.get("value"))
            for e in events
            if isinstance(e.detail.get("value"), (int, float))
        ]
        
        if numeric_events:
            min_event = min(numeric_events, key=lambda x: x[1])[0]
            max_event = max(numeric_events, key=lambda x: x[1])[0]
            add_if_new(min_event)
            add_if_new(max_event)
        
        # 5. Last event
        add_if_new(events[-1])
        
        # Sort representative by time
        representative.sort(key=lambda e: e.timestamp)
        
        return representative
    
    def _iqr(self, values: list[float]) -> float:
        """Calculate interquartile range."""
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        return sorted_vals[q3_idx] - sorted_vals[q1_idx]
    
    def get_aggregation_report(
        self,
        original_count: int,
        ungrouped_count: int,
        groups: list[EventGroup],
    ) -> dict:
        """
        Report on what aggregation did.
        For transparency and evaluation.
        """
        grouped_count = sum(g.event_count for g in groups)
        representative_count = sum(len(g.representative_events) for g in groups)
        traces_preserved = sum(len(g.member_source_traces) for g in groups)
        abnormal_in_groups = sum(
            g.summary_stats.get("abnormal_count", 0) for g in groups
        )
        
        return {
            "original_event_count": original_count,
            "ungrouped_event_count": ungrouped_count,
            "grouped_event_count": grouped_count,
            "number_of_groups": len(groups),
            "representative_events_shown": representative_count,
            "source_traces_preserved": traces_preserved,
            "abnormal_events_in_groups": abnormal_in_groups,
            "compression_ratio": round(
                1 - (ungrouped_count + representative_count) / original_count, 4
            ) if original_count > 0 else 0,
            "no_data_hidden": traces_preserved == grouped_count,
            "disclaimer": (
                "All source traces are preserved. "
                "Groups can be expanded to see every individual event. "
                "Abnormal events are never hidden."
            ),
        }