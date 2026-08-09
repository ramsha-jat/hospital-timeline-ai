from collections import defaultdict
from datetime import datetime
import statistics
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.config import get_settings
from app.timeline.schemas import (
    TimelineEvent,
    EventCategory,
    SourceTrace,
    EventGroup,
    PatientTimeline,
)


settings = get_settings()


class TimelineBuilder:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def build_timeline(
        self,
        hadm_id: int,
        include_categories: Optional[list[EventCategory]] = None,
        group_high_volume: bool = True,
    ) -> PatientTimeline:

        # 1. Load admission
        admission = await self.db.admissions.find_one({"hadm_id": hadm_id})

        if not admission:
            raise ValueError(f"Admission {hadm_id} not found")

        timeline = PatientTimeline(
            subject_id=admission["subject_id"],
            hadm_id=hadm_id,
            admission_time=admission["admittime"],
            discharge_time=admission.get("dischtime"),
        )

        # 2. Load dictionaries for labels
        lab_dict, chart_dict, dx_dict, px_dict = await self._load_dictionaries()

        # 3. Collect events
        all_events: list[TimelineEvent] = []
        cats = include_categories or list(EventCategory)

        if (
            EventCategory.ADMISSION in cats
            or EventCategory.DISCHARGE in cats
        ):
            all_events.extend(
                await self._admission_events(admission)
            )

        if EventCategory.TRANSFER in cats:
            all_events.extend(
                await self._transfer_events(hadm_id)
            )

        if (
            EventCategory.ICU_ADMISSION in cats
            or EventCategory.ICU_DISCHARGE in cats
        ):
            all_events.extend(
                await self._icu_stay_events(hadm_id)
            )

        if EventCategory.LAB_RESULT in cats:
            all_events.extend(
                await self._lab_events(hadm_id, lab_dict)
            )

        if EventCategory.MEDICATION in cats:
            all_events.extend(
                await self._medication_events(hadm_id)
            )

        if EventCategory.DIAGNOSIS in cats:
            all_events.extend(
                await self._diagnosis_events(hadm_id, dx_dict)
            )

        if EventCategory.PROCEDURE in cats:
            all_events.extend(
                await self._procedure_events(hadm_id, px_dict)
            )

        if EventCategory.ICU_OBSERVATION in cats:
            all_events.extend(
                await self._chart_events(hadm_id, chart_dict)
            )

        if EventCategory.ICU_OUTPUT in cats:
            all_events.extend(
                await self._output_events(hadm_id, chart_dict)
            )

        # 4. Sort by time
        all_events.sort(
            key=lambda e: (e.timestamp, e.category.value)
        )

        # 5. Group high-volume events
        if group_high_volume:
            events, groups = self._group_high_volume(all_events)
            timeline.events = events
            timeline.groups = groups
        else:
            timeline.events = all_events

        # 6. Quality report
        timeline.quality_report = self._quality_report(all_events)

        return timeline

    # ─────────────────────────────────────────────
    # DICTIONARIES
    # ─────────────────────────────────────────────

    async def _load_dictionaries(self):
        # Lab items
        lab_dict = {}

        async for doc in self.db.d_labitems.find({}):
            lab_dict[doc["itemid"]] = doc.get(
                "label",
                f"Lab {doc['itemid']}",
            )

        # Chart items
        chart_dict = {}

        async for doc in self.db.d_items.find({}):
            chart_dict[doc["itemid"]] = (
                doc.get(
                    "label",
                    f"Item {doc['itemid']}",
                ),
                doc.get("unitname"),
            )

        # ICD diagnoses
        dx_dict = {}

        async for doc in self.db.d_icd_diagnoses.find({}):
            key = (
                doc["icd_code"],
                doc["icd_version"],
            )

            dx_dict[key] = doc.get(
                "long_title",
                f"ICD-{doc['icd_version']} {doc['icd_code']}",
            )

        # ICD procedures
        px_dict = {}

        async for doc in self.db.d_icd_procedures.find({}):
            key = (
                doc["icd_code"],
                doc["icd_version"],
            )

            px_dict[key] = doc.get(
                "long_title",
                f"ICD-{doc['icd_version']} {doc['icd_code']}",
            )

        return lab_dict, chart_dict, dx_dict, px_dict

    # ─────────────────────────────────────────────
    # EVENT LOADERS
    # ─────────────────────────────────────────────

    async def _admission_events(
        self,
        adm: dict,
    ) -> list[TimelineEvent]:

        events = []

        doc_id = str(
            adm.get("_id", adm["hadm_id"])
        )

        # Admission event
        events.append(
            TimelineEvent(
                event_id=f"admission_{adm['hadm_id']}",
                category=EventCategory.ADMISSION,
                timestamp=adm["admittime"],
                label=f"Admission ({adm.get('admission_type', 'Unknown')})",
                detail={
                    "admission_type": adm.get("admission_type"),
                    "admission_location": adm.get(
                        "admission_location"
                    ),
                    "insurance": adm.get("insurance"),
                    "race": adm.get("race"),
                },
                source=SourceTrace(
                    collection="admissions",
                    fields=(
                        "admittime,"
                        "admission_type,"
                        "admission_location"
                    ),
                    doc_id=doc_id,
                    charttime=adm["admittime"],
                ),
            )
        )

        # Discharge event
        if adm.get("dischtime"):
            events.append(
                TimelineEvent(
                    event_id=f"discharge_{adm['hadm_id']}",
                    category=EventCategory.DISCHARGE,
                    timestamp=adm["dischtime"],
                    label=(
                        f"Discharge → "
                        f"{adm.get('discharge_location', 'Unknown')}"
                    ),
                    detail={
                        "discharge_location": adm.get(
                            "discharge_location"
                        ),
                        "hospital_expire_flag": adm.get(
                            "hospital_expire_flag"
                        ),
                    },
                    source=SourceTrace(
                        collection="admissions",
                        fields=(
                            "dischtime,"
                            "discharge_location"
                        ),
                        doc_id=doc_id,
                        charttime=adm["dischtime"],
                    ),
                )
            )

        return events

    async def _transfer_events(
        self,
        hadm_id: int,
    ) -> list[TimelineEvent]:

        events = []

        async for t in self.db.transfers.find(
            {"hadm_id": hadm_id}
        ).sort("intime", 1):

            events.append(
                TimelineEvent(
                    event_id=f"transfer_{t['transfer_id']}",
                    category=EventCategory.TRANSFER,
                    timestamp=t["intime"],
                    end_timestamp=t.get("outtime"),
                    label=(
                        f"Transfer: "
                        f"{t.get('eventtype', '?')} → "
                        f"{t.get('careunit', 'Unknown')}"
                    ),
                    detail={
                        "eventtype": t.get("eventtype"),
                        "careunit": t.get("careunit"),
                        "wardid": t.get("wardid"),
                    },
                    source=SourceTrace(
                        collection="transfers",
                        fields=(
                            "eventtype,"
                            "careunit,"
                            "intime,"
                            "outtime"
                        ),
                        doc_id=str(
                            t.get(
                                "_id",
                                t["transfer_id"],
                            )
                        ),
                        charttime=t["intime"],
                    ),
                )
            )

        return events

    async def _icu_stay_events(
        self,
        hadm_id: int,
    ) -> list[TimelineEvent]:

        events = []

        async for s in self.db.icustays.find(
            {"hadm_id": hadm_id}
        ).sort("intime", 1):

            doc_id = str(
                s.get("_id", s["stay_id"])
            )

            # ICU admission
            events.append(
                TimelineEvent(
                    event_id=f"icu_in_{s['stay_id']}",
                    category=EventCategory.ICU_ADMISSION,
                    timestamp=s["intime"],
                    label=(
                        f"ICU Admission: "
                        f"{s.get('first_careunit', 'Unknown')}"
                    ),
                    detail={
                        "careunit": s.get("first_careunit"),
                        "stay_id": s["stay_id"],
                    },
                    source=SourceTrace(
                        collection="icustays",
                        fields="first_careunit,intime",
                        doc_id=doc_id,
                        charttime=s["intime"],
                    ),
                )
            )

            # ICU discharge
            if s.get("outtime"):
                los = s.get("los", 0) or 0

                events.append(
                    TimelineEvent(
                        event_id=f"icu_out_{s['stay_id']}",
                        category=EventCategory.ICU_DISCHARGE,
                        timestamp=s["outtime"],
                        label=(
                            f"ICU Discharge: "
                            f"{s.get('last_careunit', '?')} "
                            f"(LOS: {los:.1f} days)"
                        ),
                        detail={
                            "careunit": s.get("last_careunit"),
                            "los_days": los,
                        },
                        source=SourceTrace(
                            collection="icustays",
                            fields="last_careunit,outtime,los",
                            doc_id=doc_id,
                            charttime=s["outtime"],
                        ),
                    )
                )

        return events

    async def _lab_events(
        self,
        hadm_id: int,
        lab_dict: dict,
    ) -> list[TimelineEvent]:

        events = []

        async for lab in self.db.labevents.find(
            {"hadm_id": hadm_id}
        ).sort("charttime", 1):

            itemid = lab.get("itemid", 0)

            label = lab_dict.get(
                itemid,
                f"Lab item {itemid}",
            )

            doc_id = str(
                lab.get(
                    "_id",
                    lab.get("labevent_id", "?"),
                )
            )

            # Abnormal detection
            is_abnormal = False

            flag = lab.get("flag")

            if flag and str(flag).strip():
                is_abnormal = True
            else:
                valuenum = lab.get("valuenum")
                ref_lo = lab.get("ref_range_lower")
                ref_hi = lab.get("ref_range_upper")

                if (
                    valuenum is not None
                    and ref_lo is not None
                    and ref_hi is not None
                ):
                    try:
                        is_abnormal = (
                            float(valuenum) < float(ref_lo)
                            or float(valuenum) > float(ref_hi)
                        )
                    except (ValueError, TypeError):
                        pass

            # Uncertainty
            uncertainty = None

            if (
                lab.get("valuenum") is None
                and lab.get("value") is not None
            ):
                uncertainty = "non_numeric_value"

            if lab.get("valueuom") is None:
                uncertainty = (
                    (uncertainty + ";") if uncertainty else ""
                ) + "missing_uom"

            events.append(
                TimelineEvent(
                    event_id=f"lab_{doc_id}",
                    category=EventCategory.LAB_RESULT,
                    timestamp=lab["charttime"],
                    label=label,
                    detail={
                        "itemid": itemid,
                        "value": (
                            lab.get("valuenum")
                            if lab.get("valuenum") is not None
                            else lab.get("value")
                        ),
                        "uom": lab.get("valueuom"),
                        "ref_range": (
                            [
                                lab.get("ref_range_lower"),
                                lab.get("ref_range_upper"),
                            ]
                            if lab.get("ref_range_lower") is not None
                            else None
                        ),
                        "flag": flag,
                        "label_source": "d_labitems_dictionary",
                    },
                    source=SourceTrace(
                        collection="labevents",
                        fields=(
                            "itemid,charttime,"
                            "valuenum,valueuom,flag"
                        ),
                        doc_id=doc_id,
                        charttime=lab["charttime"],
                    ),
                    is_abnormal=is_abnormal,
                    uncertainty=(
                        uncertainty.strip(";")
                        if uncertainty
                        else None
                    ),
                )
            )

        return events

    async def _medication_events(
        self,
        hadm_id: int,
    ) -> list[TimelineEvent]:

        events = []

        async for med in self.db.prescriptions.find(
            {"hadm_id": hadm_id}
        ).sort("starttime", 1):

            doc_id = str(
                med.get(
                    "_id",
                    med.get("prescription_id", "?"),
                )
            )

            drug = med.get(
                "drug",
                "Unknown drug",
            )

            dose = med.get(
                "dose_val_rx",
                "",
            )

            unit = med.get(
                "dose_unit_rx",
                "",
            )

            events.append(
                TimelineEvent(
                    event_id=f"med_{doc_id}",
                    category=EventCategory.MEDICATION,
                    timestamp=med["starttime"],
                    end_timestamp=med.get("stoptime"),
                    label=f"{drug} {dose} {unit}".strip(),
                    detail={
                        "drug": drug,
                        "dose": dose,
                        "dose_unit": unit,
                        "route": med.get("route"),
                        "label_source": (
                            "prescriptions_drug_name"
                        ),
                    },
                    source=SourceTrace(
                        collection="prescriptions",
                        fields=(
                            "drug,starttime,stoptime,"
                            "dose_val_rx,route"
                        ),
                        doc_id=doc_id,
                        charttime=med["starttime"],
                    ),
                )
            )

        return events

    async def _diagnosis_events(
        self,
        hadm_id: int,
        dx_dict: dict,
    ) -> list[TimelineEvent]:

        events = []

        async for dx in self.db.diagnoses_icd.find(
            {"hadm_id": hadm_id}
        ).sort("seq_num", 1):

            doc_id = str(
                dx.get(
                    "_id",
                    dx.get("row_id", "?"),
                )
            )

            icd_code = dx.get(
                "icd_code",
                "",
            )

            icd_version = dx.get(
                "icd_version",
                10,
            )

            long_title = dx_dict.get(
                (icd_code, icd_version),
                f"ICD-{icd_version} {icd_code}",
            )

            events.append(
                TimelineEvent(
                    event_id=f"dx_{doc_id}",
                    category=EventCategory.DIAGNOSIS,
                    timestamp=datetime.min,
                    label=f"Dx: {long_title}",
                    detail={
                        "icd_code": icd_code,
                        "icd_version": icd_version,
                        "seq_num": dx.get("seq_num"),
                        "long_title": long_title,
                        "label_source": (
                            "d_icd_diagnoses_dictionary"
                        ),
                        "disclaimer": (
                            "ICD billing code, not "
                            "clinician-authored diagnosis note"
                        ),
                    },
                    source=SourceTrace(
                        collection="diagnoses_icd",
                        fields="icd_code,icd_version,seq_num",
                        doc_id=doc_id,
                        charttime=None,
                    ),
                )
            )

        return events

    async def _procedure_events(
        self,
        hadm_id: int,
        px_dict: dict,
    ) -> list[TimelineEvent]:

        events = []

        async for px in self.db.procedures_icd.find(
            {"hadm_id": hadm_id}
        ).sort("seq_num", 1):

            doc_id = str(
                px.get(
                    "_id",
                    px.get("row_id", "?"),
                )
            )

            icd_code = px.get(
                "icd_code",
                "",
            )

            icd_version = px.get(
                "icd_version",
                10,
            )

            long_title = px_dict.get(
                (icd_code, icd_version),
                f"ICD-{icd_version} {icd_code}",
            )

            events.append(
                TimelineEvent(
                    event_id=f"px_{doc_id}",
                    category=EventCategory.PROCEDURE,
                    timestamp=datetime.min,
                    label=f"Proc: {long_title}",
                    detail={
                        "icd_code": icd_code,
                        "icd_version": icd_version,
                        "long_title": long_title,
                        "label_source": (
                            "d_icd_procedures_dictionary"
                        ),
                    },
                    source=SourceTrace(
                        collection="procedures_icd",
                        fields="icd_code,icd_version,seq_num",
                        doc_id=doc_id,
                        charttime=None,
                    ),
                )
            )

        return events

    async def _chart_events(
        self,
        hadm_id: int,
        chart_dict: dict,
    ) -> list[TimelineEvent]:

        events = []

        cursor = self.db.chartevents.find(
            {"hadm_id": hadm_id}
        ).sort("charttime", 1)

        count = 0

        async for c in cursor:

            if count >= settings.MAX_TIMELINE_EVENTS:
                break

            count += 1

            itemid = c.get(
                "itemid",
                0,
            )

            label, unit = chart_dict.get(
                itemid,
                (f"Item {itemid}", None),
            )

            doc_id = str(
                c.get(
                    "_id",
                    c.get("chartevent_id", "?"),
                )
            )

            uom = c.get("valueuom") or unit

            uncertainty = None

            if (
                c.get("valuenum") is None
                and c.get("value") is not None
            ):
                uncertainty = "non_numeric_value"

            events.append(
                TimelineEvent(
                    event_id=f"chart_{doc_id}",
                    category=EventCategory.ICU_OBSERVATION,
                    timestamp=c["charttime"],
                    label=label,
                    detail={
                        "itemid": itemid,
                        "value": (
                            c.get("valuenum")
                            if c.get("valuenum") is not None
                            else c.get("value")
                        ),
                        "uom": uom,
                        "warning": c.get("warning"),
                        "label_source": "d_items_dictionary",
                    },
                    source=SourceTrace(
                        collection="chartevents",
                        fields=(
                            "itemid,charttime,"
                            "valuenum,valueuom,warning"
                        ),
                        doc_id=doc_id,
                        charttime=c["charttime"],
                    ),
                    is_abnormal=bool(c.get("warning")),
                    uncertainty=uncertainty,
                )
            )

        return events

    async def _output_events(
        self,
        hadm_id: int,
        chart_dict: dict,
    ) -> list[TimelineEvent]:

        events = []

        async for o in self.db.outputevents.find(
            {"hadm_id": hadm_id}
        ).sort("charttime", 1):

            itemid = o.get(
                "itemid",
                0,
            )

            label, unit = chart_dict.get(
                itemid,
                (f"Item {itemid}", None),
            )

            doc_id = str(
                o.get(
                    "_id",
                    o.get("outputevent_id", "?"),
                )
            )

            events.append(
                TimelineEvent(
                    event_id=f"output_{doc_id}",
                    category=EventCategory.ICU_OUTPUT,
                    timestamp=o["charttime"],
                    label=label,
                    detail={
                        "itemid": itemid,
                        "value": o.get("value"),
                        "uom": o.get("valueuom") or unit,
                        "label_source": "d_items_dictionary",
                    },
                    source=SourceTrace(
                        collection="outputevents",
                        fields=(
                            "itemid,charttime,"
                            "value,valueuom"
                        ),
                        doc_id=doc_id,
                        charttime=o["charttime"],
                    ),
                )
            )

        return events

    # ─────────────────────────────────────────────
    # GROUPING
    # ─────────────────────────────────────────────

    def _group_high_volume(
        self,
        events: list[TimelineEvent],
    ):
        HIGH_VOL = {
            EventCategory.ICU_OBSERVATION,
            EventCategory.ICU_OUTPUT,
        }

        key_to_events: dict[
            str,
            list[TimelineEvent],
        ] = defaultdict(list)

        for e in events:
            if e.category in HIGH_VOL:
                key = (
                    f"{e.category.value}_"
                    f"{e.detail.get('itemid', 'na')}"
                )
                key_to_events[key].append(e)

        ungrouped = [
            e
            for e in events
            if e.category not in HIGH_VOL
        ]

        groups = []

        for key, evts in key_to_events.items():

            if len(evts) < settings.HIGH_VOLUME_THRESHOLD:
                ungrouped.extend(evts)
                continue

            numeric_values = [
                e.detail["value"]
                for e in evts
                if isinstance(
                    e.detail.get("value"),
                    (int, float),
                )
            ]

            summary = {}

            if numeric_values:
                summary = {
                    "count": len(numeric_values),
                    "mean": round(
                        statistics.mean(numeric_values),
                        2,
                    ),
                    "min": round(
                        min(numeric_values),
                        2,
                    ),
                    "max": round(
                        max(numeric_values),
                        2,
                    ),
                    "sd": (
                        round(
                            statistics.stdev(numeric_values),
                            2,
                        )
                        if len(numeric_values) > 1
                        else 0
                    ),
                }

            representative = [evts[0]]

            for e in evts[1:-1]:
                if e.is_abnormal:
                    representative.append(e)

            if len(evts) > 1:
                representative.append(evts[-1])

            groups.append(
                EventGroup(
                    group_id=(
                        f"group_{key}_"
                        f"{evts[0].timestamp.isoformat()}"
                    ),
                    category=evts[0].category,
                    start_time=evts[0].timestamp,
                    end_time=evts[-1].timestamp,
                    event_count=len(evts),
                    summary_stats=summary,
                    representative_events=representative,
                    is_collapsed=True,
                    member_source_traces=[
                        e.source
                        for e in evts
                    ],
                )
            )

        ungrouped.sort(
            key=lambda e: (
                e.timestamp,
                e.category.value,
            )
        )

        groups.sort(
            key=lambda g: g.start_time
        )

        return ungrouped, groups

    # ─────────────────────────────────────────────
    # QUALITY
    # ─────────────────────────────────────────────

    def _quality_report(
        self,
        events: list[TimelineEvent],
    ) -> dict:

        from collections import Counter

        category_counts = Counter(
            e.category.value
            for e in events
        )

        abnormal = sum(
            1
            for e in events
            if e.is_abnormal
        )

        uncertain = sum(
            1
            for e in events
            if e.uncertainty
        )

        sorted_ts = sorted(
            set(
                e.timestamp
                for e in events
                if e.timestamp != datetime.min
            )
        )

        gaps = []

        for i in range(1, len(sorted_ts)):
            gap_h = (
                sorted_ts[i] - sorted_ts[i - 1]
            ).total_seconds() / 3600

            if gap_h > 24:
                gaps.append(
                    {
                        "after": sorted_ts[i].isoformat(),
                        "gap_hours": round(gap_h, 1),
                    }
                )

        return {
            "total_events": len(events),
            "by_category": dict(category_counts),
            "abnormal_events": abnormal,
            "uncertain_events": uncertain,
            "temporal_gaps_over_24h": gaps,
            "disclaimer": (
                "Data quality report for research use only, "
                "not clinical assessment"
            ),
        }
