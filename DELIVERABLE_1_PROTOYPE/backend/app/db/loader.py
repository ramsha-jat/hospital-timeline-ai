# app/db/loader.py
"""Load MIMIC-IV CSV files into MongoDB — FIXED version."""
import pandas as pd
import numpy as np
from pymongo import MongoClient
from datetime import datetime, timedelta
from pathlib import Path
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

MONGODB_URI = "mongodb+srv://ramshabscsf19:xNKxr8MjSeGEr87z@cluster0.8keb21y.mongodb.net/"
MONGODB_DATABASE = "curelens_ai"

DATE_COLUMNS = {
    "patients": ["dod"],
    "admissions": ["admittime", "dischtime", "deathtime"],
    "icustays": ["intime", "outtime"],
    "transfers": ["intime", "outtime"],
    "labevents": ["charttime", "storetime"],
    "prescriptions": ["starttime", "stoptime"],
    "chartevents": ["charttime", "storetime"],
    "outputevents": ["charttime", "storetime"],
    "inputevents_mv": ["starttime", "stoptime", "storetime"],
}

TABLE_FILES = {
    # hosp/ folder files
    "patients":         ("hosp", "patients.csv.gz"),
    "admissions":       ("hosp", "admissions.csv.gz"),
    "transfers":        ("hosp", "transfers.csv.gz"),
    "prescriptions":    ("hosp", "prescriptions.csv.gz"),
    "diagnoses_icd":    ("hosp", "diagnoses_icd.csv.gz"),
    "procedures_icd":   ("hosp", "procedures_icd.csv.gz"),
    "labevents":        ("hosp", "labevents.csv.gz"),
    "d_labitems":       ("hosp", "d_labitems.csv.gz"),
    "d_icd_diagnoses":  ("hosp", "d_icd_diagnoses.csv.gz"),
    "d_icd_procedures": ("hosp", "d_icd_procedures.csv.gz"),
    # icu/ folder files
    "icustays":         ("icu",  "icustays.csv.gz"),
    "chartevents":      ("icu",  "chartevents.csv.gz"),
    "outputevents":     ("icu",  "outputevents.csv.gz"),
    "inputevents_mv":   ("icu",  "inputevents_mv.csv.gz"),
    "d_items":          ("icu",  "d_items.csv.gz"),
}


def clean_record(record: dict) -> dict:
    """
    FIX: Convert NaT, NaN, numpy types to None/Python types
    so MongoDB can store them properly.
    """
    cleaned = {}
    for key, value in record.items():
        # pandas NaT → None
        if pd.isna(value):
            cleaned[key] = None
        # numpy int → Python int
        elif isinstance(value, (np.integer,)):
            cleaned[key] = int(value)
        # numpy float → Python float (but check nan)
        elif isinstance(value, (np.floating,)):
            if np.isnan(value) or np.isinf(value):
                cleaned[key] = None
            else:
                cleaned[key] = float(value)
        # numpy bool → Python bool
        elif isinstance(value, (np.bool_,)):
            cleaned[key] = bool(value)
        # pandas Timestamp → Python datetime
        elif isinstance(value, pd.Timestamp):
            if pd.isna(value):
                cleaned[key] = None
            else:
                cleaned[key] = value.to_pydatetime()
        # already good
        else:
            cleaned[key] = value
    return cleaned


def load_mimic_to_mongodb(csv_dir: str):
    print("=" * 60)
    print("MIMIC-IV → MongoDB Loader (Fixed)")
    print("=" * 60)
    print(f"Source: {csv_dir}")
    print(f"Target: {MONGODB_DATABASE} on Atlas")
    print()

    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]

    try:
        client.admin.command("ping")
        print("✅ Connected to MongoDB Atlas")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    csv_path = Path(csv_dir)

    if not csv_path.exists():
        print(f"❌ Directory not found: {csv_dir}")
        return

    total_docs = 0
    failed_tables = []

    for collection_name, (subfolder, filename) in TABLE_FILES.items():
        # Try multiple paths
        possible_paths = [
            csv_path / subfolder / filename,
            csv_path / subfolder / filename.replace(".gz", ""),
            csv_path / filename,
            csv_path / filename.replace(".gz", ""),
            csv_path / "mimic-iv-demo-2.2" / subfolder / filename,
            csv_path / "mimic-iv-demo-2.2" / subfolder / filename.replace(".gz", ""),
        ]

        filepath = None
        for p in possible_paths:
            if p.exists():
                filepath = p
                break

        if filepath is None:
            print(f"  ⚠️  {subfolder}/{filename} not found, skipping")
            failed_tables.append(collection_name)
            continue

        print(f"  Loading {filepath.name} → {collection_name}...")

        try:
            compression = "gzip" if filepath.name.endswith(".gz") else None
            df = pd.read_csv(filepath, compression=compression)

            # Parse dates
            date_cols = DATE_COLUMNS.get(collection_name, [])
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

            # Convert to records and CLEAN each one
            raw_records = df.to_dict(orient="records")
            records = [clean_record(r) for r in raw_records]

            # Drop existing collection and insert
            db.drop_collection(collection_name)

            batch_size = 5000
            inserted = 0
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                try:
                    result = db[collection_name].insert_many(batch, ordered=False)
                    inserted += len(result.inserted_ids)
                except Exception as e:
                    print(f"    ⚠️  Batch {i}: {str(e)[:80]}")

            # Create indexes
            if "hadm_id" in df.columns:
                db[collection_name].create_index("hadm_id")
            if "subject_id" in df.columns:
                db[collection_name].create_index("subject_id")
            if "itemid" in df.columns:
                db[collection_name].create_index("itemid")
            if "charttime" in df.columns:
                db[collection_name].create_index("charttime")

            total_docs += inserted
            print(f"  ✅ {collection_name}: {inserted} docs")

        except Exception as e:
            print(f"  ❌ {collection_name} FAILED: {str(e)[:100]}")
            failed_tables.append(collection_name)

    print()
    print("=" * 60)
    print(f"✅ Done! Total: {total_docs} documents loaded")
    if failed_tables:
        print(f"⚠️  Missing/Failed: {failed_tables}")
    print(f"   Database: {MONGODB_DATABASE}")
    print("=" * 60)

    client.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    else:
        data_path = input("Enter path to MIMIC-IV data folder: ")

    load_mimic_to_mongodb(data_path)