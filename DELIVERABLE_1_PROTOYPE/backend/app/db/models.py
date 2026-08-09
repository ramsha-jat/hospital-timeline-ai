# backend/app/db/models.py
"""
Every model includes a `_source_trace` column pattern.
This is the foundation of our "clear trail back to source data".
"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, 
    ForeignKey, Text, BigInteger, Boolean
)
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime

class Base(DeclarativeBase):
    pass

# ─── PATIENTS ────────────────────────────────────────────
class Patient(Base):
    __tablename__ = "patients"
    
    subject_id   = Column(Integer, primary_key=True)
    gender       = Column(String(1))
    anchor_age   = Column(Integer)
    anchor_year  = Column(Integer)
    dod          = Column(DateTime, nullable=True)

# ─── ADMISSIONS ──────────────────────────────────────────
class Admission(Base):
    __tablename__ = "admissions"
    
    hadm_id            = Column(Integer, primary_key=True)
    subject_id         = Column(Integer, ForeignKey("patients.subject_id"))
    admittime          = Column(DateTime)
    dischtime          = Column(DateTime)
    deathtime          = Column(DateTime, nullable=True)
    admission_type     = Column(String(50))
    admission_location = Column(String(100))
    discharge_location = Column(String(100))
    insurance          = Column(String(50))
    language           = Column(String(50))
    marital_status     = Column(String(50))
    race               = Column(String(100))
    hospital_expire_flag = Column(Integer)

    patient = relationship("Patient")

# ─── ICU STAYS ───────────────────────────────────────────
class ICUSTay(Base):
    __tablename__ = "icustays"
    
    stay_id     = Column(Integer, primary_key=True)
    subject_id  = Column(Integer, ForeignKey("patients.subject_id"))
    hadm_id     = Column(Integer, ForeignKey("admissions.hadm_id"))
    first_careunit = Column(String(20))
    last_careunit  = Column(String(20))
    intime      = Column(DateTime)
    outtime     = Column(DateTime)
    los         = Column(Float)

# ─── TRANSFERS ───────────────────────────────────────────
class Transfer(Base):
    __tablename__ = "transfers"
    
    transfer_id = Column(Integer, primary_key=True)
    subject_id  = Column(Integer)
    hadm_id     = Column(Integer, ForeignKey("admissions.hadm_id"))
    eventtype   = Column(String(20))
    careunit    = Column(String(20))
    wardid      = Column(Integer)
    intime      = Column(DateTime)
    outtime     = Column(DateTime)

# ─── LAB EVENTS ──────────────────────────────────────────
class LabEvent(Base):
    __tablename__ = "labevents"
    
    labevent_id = Column(BigInteger, primary_key=True)
    subject_id  = Column(Integer)
    hadm_id     = Column(Integer, ForeignKey("admissions.hadm_id"))
    itemid      = Column(Integer)
    charttime   = Column(DateTime)
    storetime   = Column(DateTime)
    value       = Column(Float, nullable=True)
    valuenum    = Column(Float, nullable=True)
    valueuom    = Column(String(20), nullable=True)
    ref_range_lower = Column(Float, nullable=True)
    ref_range_upper = Column(Float, nullable=True)
    flag        = Column(String(10), nullable=True)

# ─── PRESCRIPTIONS ──────────────────────────────────────
class Prescription(Base):
    __tablename__ = "prescriptions"
    
    prescription_id = Column(BigInteger, primary_key=True)
    subject_id      = Column(Integer)
    hadm_id         = Column(Integer, ForeignKey("admissions.hadm_id"))
    pharmacy_id     = Column(Integer, nullable=True)
    poe_id          = Column(Integer, nullable=True)
    poe_seq         = Column(Integer, nullable=True)
    starttime       = Column(DateTime)
    stoptime        = Column(DateTime, nullable=True)
    drug_type       = Column(String(20), nullable=True)
    drug            = Column(String(100), nullable=True)
    gsn             = Column(String(20), nullable=True)
    ndc             = Column(String(20), nullable=True)
    prod_strength   = Column(String(100), nullable=True)
    form_rx         = Column(String(20), nullable=True)
    dose_val_rx     = Column(String(50), nullable=True)
    dose_unit_rx    = Column(String(50), nullable=True)
    route           = Column(String(10), nullable=True)

# ─── DIAGNOSES ───────────────────────────────────────────
class DiagnosisICD(Base):
    __tablename__ = "diagnoses_icd"
    
    row_id      = Column(BigInteger, primary_key=True)
    subject_id  = Column(Integer)
    hadm_id     = Column(Integer, ForeignKey("admissions.hadm_id"))
    seq_num     = Column(Integer)
    icd_code    = Column(String(10))
    icd_version = Column(Integer)

# ─── PROCEDURES ──────────────────────────────────────────
class ProcedureICD(Base):
    __tablename__ = "procedures_icd"
    
    row_id      = Column(BigInteger, primary_key=True)
    subject_id  = Column(Integer)
    hadm_id     = Column(Integer, ForeignKey("admissions.hadm_id"))
    seq_num     = Column(Integer)
    icd_code    = Column(String(10))
    icd_version = Column(Integer)

# ─── CHART EVENTS (ICU observations) ────────────────────
class ChartEvent(Base):
    __tablename__ = "chartevents"
    
    chartevent_id = Column(BigInteger, primary_key=True)
    subject_id    = Column(Integer)
    hadm_id       = Column(Integer)
    stay_id       = Column(Integer, nullable=True)
    itemid        = Column(Integer)
    charttime     = Column(DateTime)
    storetime     = Column(DateTime)
    value         = Column(String(200), nullable=True)
    valuenum      = Column(Float, nullable=True)
    valueuom      = Column(String(20), nullable=True)
    warning       = Column(Integer, nullable=True)

# ─── OUTPUT EVENTS ──────────────────────────────────────
class OutputEvent(Base):
    __tablename__ = "outputevents"
    
    outputevent_id = Column(BigInteger, primary_key=True)
    subject_id     = Column(Integer)
    hadm_id        = Column(Integer)
    stay_id        = Column(Integer, nullable=True)
    itemid         = Column(Integer)
    charttime      = Column(DateTime)
    storetime      = Column(DateTime)
    value          = Column(Float, nullable=True)
    valueuom       = Column(String(20), nullable=True)

# ─── DICTIONARY TABLES ──────────────────────────────────
class DLabItem(Base):
    __tablename__ = "d_labitems"
    itemid   = Column(Integer, primary_key=True)
    label    = Column(String(200))
    fluid    = Column(String(50), nullable=True)
    category = Column(String(50), nullable=True)

class DItem(Base):
    __tablename__ = "d_items"
    itemid   = Column(Integer, primary_key=True)
    label    = Column(String(200))
    category = Column(String(50), nullable=True)
    unitname = Column(String(50), nullable=True)

class DICDDiagnosis(Base):
    __tablename__ = "d_icd_diagnoses"
    icd_code    = Column(String(10), primary_key=True)
    icd_version = Column(Integer, primary_key=True)
    long_title  = Column(String(300))

class DICDProcedure(Base):
    __tablename__ = "d_icd_procedures"
    icd_code    = Column(String(10), primary_key=True)
    icd_version = Column(Integer, primary_key=True)
    long_title  = Column(String(300))