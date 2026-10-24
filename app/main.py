"""Dental Hospital & Research Centre demonstration backend.

All patient and trial records created by the built-in seed are fictional.
This application is NOT an EHR/EDC validated for clinical deployment.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from itsdangerous import BadSignature, URLSafeTimedSerializer
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///{(BASE_DIR.parent / 'dental_demo.db').as_posix()}")
if DATABASE_URL.startswith(('postgres://', 'postgresql://')):
    DATABASE_URL = 'postgresql+psycopg://' + DATABASE_URL.split('://', 1)[1]
SECRET_KEY = os.getenv('SECRET_KEY', 'local-demo-unsafe-change-for-real-deployment')
COOKIE_SECURE = os.getenv('COOKIE_SECURE', 'false').lower() == 'true'
DEMO_SEED = os.getenv('DEMO_SEED', 'true').lower() == 'true'
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, autoflush=False, expire_on_commit=False)
signer = URLSafeTimedSerializer(SECRET_KEY, salt='dental-demo-session-v1')


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    pw_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(30))
    requested_role: Mapped[str] = mapped_column(String(30), default='receptionist')
    status: Mapped[str] = mapped_column(String(24), default='ACTIVE')
    session_epoch: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class UserPermission(Base):
    __tablename__ = 'user_permissions'
    __table_args__ = (UniqueConstraint('user_id', 'module', name='uq_user_module'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    module: Mapped[str] = mapped_column(String(50))
    access: Mapped[str] = mapped_column(String(10))


class Patient(Base):
    __tablename__ = 'patients'
    id: Mapped[int] = mapped_column(primary_key=True)
    mrn: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    dob: Mapped[str] = mapped_column(String(10))
    gender: Mapped[str] = mapped_column(String(30), default='Not specified')
    phone: Mapped[str] = mapped_column(String(30), default='')
    allergies: Mapped[str] = mapped_column(Text, default='')
    medical_history: Mapped[str] = mapped_column(Text, default='')
    medical_alerts: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Encounter(Base):
    __tablename__ = 'encounters'
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id'))
    seen_on: Mapped[str] = mapped_column(String(10))
    dentist: Mapped[str] = mapped_column(String(120))
    complaint: Mapped[str] = mapped_column(Text)
    diagnosis: Mapped[str] = mapped_column(Text, default='')
    vital_notes: Mapped[str] = mapped_column(Text, default='')
    clinical_notes: Mapped[str] = mapped_column(Text, default='')


class Finding(Base):
    __tablename__ = 'findings'
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id'))
    tooth: Mapped[str] = mapped_column(String(2))
    surface: Mapped[str] = mapped_column(String(50), default='All')
    finding: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(30), default='Mild')
    probing_mm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bleeding: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default='')


class CarePlan(Base):
    __tablename__ = 'care_plans'
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id'))
    trial_id: Mapped[int | None] = mapped_column(ForeignKey('trials.id'), nullable=True)
    tooth: Mapped[str] = mapped_column(String(2), default='')
    diagnosis: Mapped[str] = mapped_column(Text)
    procedure: Mapped[str] = mapped_column(String(160))
    sequence: Mapped[str] = mapped_column(String(80), default='Definitive care')
    priority: Mapped[str] = mapped_column(String(30), default='Routine')
    estimated_cost: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(30), default='DRAFT')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Appointment(Base):
    __tablename__ = 'appointments'
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id'))
    scheduled_at: Mapped[str] = mapped_column(String(20))
    provider: Mapped[str] = mapped_column(String(100))
    purpose: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default='Scheduled')
    notes: Mapped[str] = mapped_column(Text, default='')


class Procedure(Base):
    __tablename__ = 'procedures'
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id'))
    plan_id: Mapped[int] = mapped_column(ForeignKey('care_plans.id'))
    performed_on: Mapped[str] = mapped_column(String(10))
    clinician: Mapped[str] = mapped_column(String(100))
    performed: Mapped[str] = mapped_column(String(160))
    outcome: Mapped[str] = mapped_column(String(60), default='Completed')
    instructions: Mapped[str] = mapped_column(Text, default='')
    follow_up_on: Mapped[str] = mapped_column(String(10), default='')


class Imaging(Base):
    __tablename__ = 'imaging'
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id'))
    modality: Mapped[str] = mapped_column(String(60))
    tooth: Mapped[str] = mapped_column(String(2), default='')
    captured_on: Mapped[str] = mapped_column(String(10))
    reference: Mapped[str] = mapped_column(String(150), default='')
    impression: Mapped[str] = mapped_column(Text, default='')


class LabOrder(Base):
    __tablename__ = 'lab_orders'
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id'))
    plan_id: Mapped[int] = mapped_column(ForeignKey('care_plans.id'))
    work_type: Mapped[str] = mapped_column(String(100))
    laboratory: Mapped[str] = mapped_column(String(120))
    due_on: Mapped[str] = mapped_column(String(10))
    shade: Mapped[str] = mapped_column(String(20), default='')
    status: Mapped[str] = mapped_column(String(30), default='Ordered')


class Invoice(Base):
    __tablename__ = 'invoices'
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id'))
    plan_id: Mapped[int | None] = mapped_column(ForeignKey('care_plans.id'), nullable=True)
    description: Mapped[str] = mapped_column(String(160))
    amount: Mapped[float] = mapped_column(Float)
    paid: Mapped[float] = mapped_column(Float, default=0)
    created_on: Mapped[str] = mapped_column(String(10))


class Stock(Base):
    __tablename__ = 'stock'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(60))
    batch: Mapped[str] = mapped_column(String(60), default='')
    quantity: Mapped[float] = mapped_column(Float, default=0)
    reorder_point: Mapped[float] = mapped_column(Float, default=0)
    unit: Mapped[str] = mapped_column(String(30), default='units')
    expiry: Mapped[str] = mapped_column(String(10), default='')


class Trial(Base):
    __tablename__ = 'trials'
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    title: Mapped[str] = mapped_column(String(240))
    indication: Mapped[str] = mapped_column(String(150))
    intervention: Mapped[str] = mapped_column(String(240))
    primary_endpoint: Mapped[str] = mapped_column(Text, default='')
    design: Mapped[str] = mapped_column(String(100), default='Interventional')
    ec_reference: Mapped[str] = mapped_column(String(120), default='')
    registry_reference: Mapped[str] = mapped_column(String(120), default='')
    regulatory_required: Mapped[bool] = mapped_column(Boolean, default=False)
    regulatory_reference: Mapped[str] = mapped_column(String(120), default='')
    status: Mapped[str] = mapped_column(String(30), default='DRAFT')


class Consent(Base):
    __tablename__ = 'consents'
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id'))
    trial_id: Mapped[int] = mapped_column(ForeignKey('trials.id'))
    document_version: Mapped[str] = mapped_column(String(40))
    signed_on: Mapped[str] = mapped_column(String(10))
    obtained_by: Mapped[str] = mapped_column(String(100))
    document_reference: Mapped[str] = mapped_column(String(160))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    withdrawn: Mapped[bool] = mapped_column(Boolean, default=False)


class Screening(Base):
    __tablename__ = 'screenings'
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id'))
    trial_id: Mapped[int] = mapped_column(ForeignKey('trials.id'))
    screened_on: Mapped[str] = mapped_column(String(10))
    eligibility: Mapped[str] = mapped_column(String(30))
    inclusion_exclusion_notes: Mapped[str] = mapped_column(Text)
    reviewer: Mapped[str] = mapped_column(String(100))


class Enrollment(Base):
    __tablename__ = 'enrollments'
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id'))
    trial_id: Mapped[int] = mapped_column(ForeignKey('trials.id'))
    subject_code: Mapped[str] = mapped_column(String(40), unique=True)
    enrolled_on: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(30), default='ACTIVE')


class ResearchVisit(Base):
    __tablename__ = 'research_visits'
    id: Mapped[int] = mapped_column(primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey('enrollments.id'))
    visit_name: Mapped[str] = mapped_column(String(80))
    visit_on: Mapped[str] = mapped_column(String(10))
    probing_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    plaque_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    bleeding_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    dmft: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pain_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default='')


class SafetyEvent(Base):
    __tablename__ = 'safety_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey('enrollments.id'))
    onset_on: Mapped[str] = mapped_column(String(10))
    description: Mapped[str] = mapped_column(Text)
    serious: Mapped[bool] = mapped_column(Boolean, default=False)
    severity: Mapped[str] = mapped_column(String(40))
    relatedness: Mapped[str] = mapped_column(String(80), default='Not assessed')
    status: Mapped[str] = mapped_column(String(40), default='OPEN')
    reported_on: Mapped[str] = mapped_column(String(10), default='')
    outcome: Mapped[str] = mapped_column(String(80), default='Unknown')


class Audit(Base):
    __tablename__ = 'audit'
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    actor: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(50))
    entity: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int] = mapped_column(Integer)
    detail: Mapped[str] = mapped_column(String(250), default='')


TABLES = {
    'patients': Patient, 'encounters': Encounter, 'findings': Finding, 'care-plans': CarePlan,
    'appointments': Appointment, 'procedures': Procedure, 'imaging': Imaging,
    'lab-orders': LabOrder, 'invoices': Invoice, 'stock': Stock, 'trials': Trial,
    'consents': Consent, 'screenings': Screening, 'enrollments': Enrollment,
    'research-visits': ResearchVisit, 'safety-events': SafetyEvent, 'audit': Audit,
}
ROLES = {'admin', 'dentist', 'researcher', 'coordinator', 'receptionist'}
SIGNUP_ROLES = ROLES - {'admin'}
MODULES = ['dashboard','patients','encounters','findings','care-plans','appointments',
           'procedures','imaging','lab-orders','trials','consents','screenings',
           'enrollments','research-visits','safety-events','invoices','stock','audit','users']
# RBAC role defaults. Individual staff overrides can narrow or expand any non-admin
# functional module. Audit and account administration are deliberately admin-only.
ROLE_WRITES = {
    'dentist': {'patients','encounters','findings','care-plans','appointments','procedures','imaging','lab-orders','stock','safety-events'},
    'researcher': {'trials','consents','screenings','enrollments','research-visits','safety-events'},
    'coordinator': {'appointments','consents','screenings','enrollments','research-visits','safety-events'},
    'receptionist': {'patients','appointments','invoices'},
}
ROLE_READS = {
    'dentist': {'dashboard','patients','encounters','findings','care-plans','appointments','procedures','imaging','lab-orders','stock','trials','safety-events'},
    'researcher': {'dashboard','patients','encounters','findings','care-plans','procedures','imaging','trials','consents','screenings','enrollments','research-visits','safety-events'},
    'coordinator': {'dashboard','patients','appointments','trials','consents','screenings','enrollments','research-visits','safety-events'},
    'receptionist': {'dashboard','patients','appointments','invoices'},
}


def default_access(role: str, module: str) -> str:
    if role == 'admin': return 'write'
    if module in ('audit', 'users'): return 'none'
    if module in ROLE_WRITES.get(role, set()): return 'write'
    if module in ROLE_READS.get(role, set()): return 'read'
    return 'none'


def permissions_for(db: Session, user: User) -> dict[str, dict[str, bool]]:
    overrides = {p.module: p.access for p in db.scalars(
        select(UserPermission).where(UserPermission.user_id == user.id))}
    result = {}
    for module in MODULES:
        level = default_access(user.role, module)
        if user.role != 'admin' and module not in ('users', 'audit'):
            level = overrides.get(module, level)
        result[module] = {'view': level in ('read', 'write'), 'write': level == 'write'}
    return result


def authorize(db: Session, user: User, module: str, action: str = 'write'):
    if user.status != 'ACTIVE': raise HTTPException(403, 'Account is not active')
    rights = permissions_for(db, user).get(module)
    if not rights or not rights['view' if action == 'view' else 'write']:
        raise HTTPException(403, f'No {action} permission for {module}')


def admin_only(db: Session, user: User):
    authorize(db, user, 'users', 'write')


def user_payload(db: Session, user: User) -> dict[str, Any]:
    return {'id': user.id, 'username': user.username, 'display_name': user.display_name,
            'role': user.role, 'requested_role': user.requested_role, 'status': user.status,
            'permissions': permissions_for(db, user)}
ALLOWED_TEETH = {f'{a}{b}' for a in [1, 2, 3, 4] for b in range(1, 9)} | {f'{a}{b}' for a in [5, 6, 7, 8] for b in range(1, 6)}


def as_dict(obj):
    return {column.name: (value.isoformat() if isinstance((value := getattr(obj, column.name)), (datetime, date)) else value) for column in obj.__table__.columns}


def hash_password(password: str):
    salt = secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 260000)
    return f'{salt.hex()}${hashed.hex()}'


def verify_password(password: str, password_hash: str):
    try:
        salt, target = password_hash.split('$')
        calc = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 260000)
        return hmac.compare_digest(calc, bytes.fromhex(target))
    except (ValueError, TypeError):
        return False


def get_db():
    with SessionLocal() as db:
        yield db


def current_user(request: Request, db: Session = Depends(get_db)):
    cookie = request.cookies.get('dental_session')
    if not cookie:
        raise HTTPException(401, 'Please log in')
    try:
        token = signer.loads(cookie, max_age=8 * 3600)
        user_id_str, epoch_str = token.split(':', 1)
        user_id, epoch = int(user_id_str), int(epoch_str)
    except (BadSignature, ValueError, AttributeError):
        raise HTTPException(401, 'Session expired. Please log in')
    user = db.get(User, user_id)
    if not user or user.session_epoch != epoch or user.status != 'ACTIVE':
        raise HTTPException(401, 'Session revoked or account inactive')
    # Same-origin CSRF safeguard for state changes; no external origins allowed.
    if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
        origin = request.headers.get('origin')
        if origin and origin.rstrip('/') != str(request.base_url).rstrip('/'):
            raise HTTPException(403, 'Cross-origin action blocked')
    return user


def get_or_404(db: Session, table, item_id: int):
    item = db.get(table, item_id)
    if not item:
        raise HTTPException(404, 'Record not found')
    return item


def audit(db: Session, user: User | str, action: str, obj: Any, detail: str = ''):
    db.add(Audit(actor=user if isinstance(user, str) else user.username, action=action,
                 entity=obj.__tablename__, entity_id=obj.id, detail=detail[:250]))


def save(db: Session, user: User, obj: Any, detail=''):
    db.add(obj)
    try:
        db.flush()
        audit(db, user, 'CREATE', obj, detail)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Duplicate or invalid reference')
    db.refresh(obj)
    return as_dict(obj)


def parse_date(value: str, label='date'):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise HTTPException(422, f'Invalid {label}; use YYYY-MM-DD')


def valid_tooth(value: str, optional=True):
    if value == '' and optional:
        return value
    if value not in ALLOWED_TEETH:
        raise HTTPException(422, 'FDI tooth code must be 11–48 or 51–85 (valid quadrants/positions)')
    return value


def validate_patient(db: Session, patient_id: int):
    return get_or_404(db, Patient, patient_id)


def active_consent(db: Session, patient_id: int, trial_id: int):
    return db.scalars(select(Consent).where(Consent.patient_id == patient_id, Consent.trial_id == trial_id,
                                             Consent.verified.is_(True), Consent.withdrawn.is_(False)).order_by(Consent.id.desc())).first()


def enrolled(db: Session, patient_id: int, trial_id: int):
    return db.scalars(select(Enrollment).where(Enrollment.patient_id == patient_id, Enrollment.trial_id == trial_id)).first()


class LoginIn(BaseModel):
    username: str
    password: str


class SignupIn(BaseModel):
    display_name: str = Field(min_length=2, max_length=100)
    username: str = Field(min_length=4, max_length=40, pattern=r'^[a-zA-Z][a-zA-Z0-9_.-]{3,39}$')
    password: str = Field(min_length=12, max_length=128)
    confirm_password: str
    requested_role: Literal['dentist', 'researcher', 'coordinator', 'receptionist']


class ReviewUserIn(BaseModel):
    role: Literal['admin', 'dentist', 'researcher', 'coordinator', 'receptionist']
    status: Literal['ACTIVE', 'PENDING', 'SUSPENDED']


class UserPermissionIn(BaseModel):
    module: str
    access: Literal['default', 'none', 'read', 'write']


class PatientIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    dob: str
    gender: str = 'Not specified'
    phone: str = ''
    allergies: str = ''
    medical_history: str = ''
    medical_alerts: str = ''


class EncounterIn(BaseModel):
    patient_id: int
    seen_on: str
    dentist: str = Field(min_length=2)
    complaint: str = Field(min_length=3)
    diagnosis: str = ''
    vital_notes: str = ''
    clinical_notes: str = ''


class FindingIn(BaseModel):
    patient_id: int
    tooth: str
    surface: str = 'All'
    finding: str = Field(min_length=2)
    severity: str = 'Mild'
    probing_mm: int | None = Field(default=None, ge=0, le=15)
    bleeding: bool = False
    notes: str = ''


class PlanIn(BaseModel):
    patient_id: int
    trial_id: int | None = None
    tooth: str = ''
    diagnosis: str = Field(min_length=2)
    procedure: str = Field(min_length=2)
    sequence: str = 'Definitive care'
    priority: str = 'Routine'
    estimated_cost: float = Field(default=0, ge=0)


class StatusIn(BaseModel):
    status: str


class AppointmentIn(BaseModel):
    patient_id: int
    scheduled_at: str
    provider: str
    purpose: str
    notes: str = ''


class ProcedureIn(BaseModel):
    patient_id: int
    plan_id: int
    performed_on: str
    clinician: str
    performed: str
    outcome: str = 'Completed'
    instructions: str = ''
    follow_up_on: str = ''


class ImagingIn(BaseModel):
    patient_id: int
    modality: str
    tooth: str = ''
    captured_on: str
    reference: str = ''
    impression: str = ''


class LabIn(BaseModel):
    patient_id: int
    plan_id: int
    work_type: str
    laboratory: str
    due_on: str
    shade: str = ''


class InvoiceIn(BaseModel):
    patient_id: int
    plan_id: int | None = None
    description: str
    amount: float = Field(gt=0)
    paid: float = Field(default=0, ge=0)
    created_on: str


class PaymentIn(BaseModel):
    amount: float = Field(gt=0)


class StockIn(BaseModel):
    name: str
    category: str = 'Consumables'
    batch: str = ''
    quantity: float = Field(ge=0)
    reorder_point: float = Field(ge=0)
    unit: str = 'units'
    expiry: str = ''


class StockUseIn(BaseModel):
    amount: float = Field(gt=0)
    purpose: str = Field(min_length=3)


class TrialIn(BaseModel):
    code: str = Field(min_length=3)
    title: str = Field(min_length=5)
    indication: str
    intervention: str
    primary_endpoint: str = ''
    design: str = 'Interventional'
    ec_reference: str = ''
    registry_reference: str = ''
    regulatory_required: bool = False
    regulatory_reference: str = ''


class TrialApprovalIn(BaseModel):
    status: str
    ec_reference: str = ''
    registry_reference: str = ''
    regulatory_reference: str = ''


class ConsentIn(BaseModel):
    patient_id: int
    trial_id: int
    document_version: str
    signed_on: str
    obtained_by: str
    document_reference: str
    verified: bool


class ScreeningIn(BaseModel):
    patient_id: int
    trial_id: int
    screened_on: str
    eligibility: str
    inclusion_exclusion_notes: str = Field(min_length=5)
    reviewer: str


class EnrollmentIn(BaseModel):
    patient_id: int
    trial_id: int
    enrolled_on: str


class ResearchVisitIn(BaseModel):
    enrollment_id: int
    visit_name: str
    visit_on: str
    probing_mm: float | None = Field(default=None, ge=0, le=15)
    plaque_index: float | None = Field(default=None, ge=0)
    bleeding_pct: float | None = Field(default=None, ge=0, le=100)
    dmft: int | None = Field(default=None, ge=0, le=32)
    pain_score: int | None = Field(default=None, ge=0, le=10)
    notes: str = ''


class SafetyIn(BaseModel):
    enrollment_id: int
    onset_on: str
    description: str = Field(min_length=3)
    serious: bool = False
    severity: str = 'Mild'
    relatedness: str = 'Not assessed'
    outcome: str = 'Unknown'


class SafetyUpdateIn(BaseModel):
    status: str
    reported_on: str = ''
    outcome: str = 'Unknown'


app = FastAPI(title='Dental Hospital & Research Centre', version='2.0.0',
              description='Educational demo for dental care and clinical research. Not a validated clinical system.')


@app.on_event('startup')
def startup():
    if os.getenv('RENDER', '').lower() == 'true':
        if not COOKIE_SECURE or SECRET_KEY == 'local-demo-unsafe-change-for-real-deployment':
            raise RuntimeError('Render requires COOKIE_SECURE=true and a generated SECRET_KEY.')
        if DEMO_SEED and len(os.getenv('DEMO_PASSWORD', '')) < 12:
            raise RuntimeError('Set a private DEMO_PASSWORD of at least 12 characters on Render.')
    # Lightweight additive migration for existing v1 demonstration databases.
    # Production systems should use reviewed, versioned Alembic migrations.
    if inspect(engine).has_table('users'):
        existing = {c['name'] for c in inspect(engine).get_columns('users')}
        migration = {'requested_role': "VARCHAR(30) NOT NULL DEFAULT 'receptionist'",
                     'status': "VARCHAR(24) NOT NULL DEFAULT 'ACTIVE'",
                     'session_epoch': 'INTEGER NOT NULL DEFAULT 0',
                     'created_at': 'TIMESTAMP NULL'}
        with engine.begin() as conn:
            for column, type_ in migration.items():
                if column not in existing:
                    conn.execute(text(f'ALTER TABLE users ADD COLUMN {column} {type_}'))
            if 'requested_role' not in existing:
                conn.execute(text('UPDATE users SET requested_role = role'))
    Base.metadata.create_all(engine)
    if DEMO_SEED:
        with SessionLocal() as db:
            if not db.scalar(select(func.count()).select_from(User)):
                seed_demo(db)


@app.get('/')
def index():
    return FileResponse(BASE_DIR / 'static' / 'index.html')


@app.get('/static/{filename}')
def static(filename: str):
    if filename not in {'app.css', 'app.js'}:
        raise HTTPException(404)
    return FileResponse(BASE_DIR / 'static' / filename)


@app.get('/api/health')
def health():
    return {'status': 'ok', 'mode': 'demo', 'compliance_validated': False}


@app.post('/api/signup', status_code=201)
def signup(body: SignupIn, db: Session = Depends(get_db)):
    if body.password != body.confirm_password:
        raise HTTPException(422, 'Passwords do not match')
    password = body.password
    if not any(c.islower() for c in password) or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
        raise HTTPException(422, 'Use 12+ characters with uppercase, lowercase, and a digit')
    username = body.username.strip().lower()
    if db.scalar(select(User.id).where(User.username == username)):
        raise HTTPException(409, 'Username is already taken')
    obj = User(username=username, display_name=body.display_name.strip(),
               pw_hash=hash_password(password), role=body.requested_role,
               requested_role=body.requested_role, status='PENDING')
    try:
        db.add(obj)
        db.flush()
        audit(db, username, 'SIGNUP', obj, 'Pending administrator approval; requested ' + body.requested_role)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Username is already taken')
    return {'message': 'Registration submitted. An administrator must approve your account before you can sign in.',
            'status': 'PENDING'}


@app.post('/api/login')
def login(body: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == body.username.strip().lower()))
    if not user or not verify_password(body.password, user.pw_hash):
        raise HTTPException(401, 'Invalid username or password')
    if user.status != 'ACTIVE':
        raise HTTPException(403, 'Account is pending administrator approval' if user.status == 'PENDING'
                            else 'Account is suspended; contact the administrator')
    response.set_cookie('dental_session', signer.dumps(f'{user.id}:{user.session_epoch}'), httponly=True,
                        secure=COOKIE_SECURE, samesite='strict', max_age=8 * 3600, path='/')
    return user_payload(db, user)


@app.post('/api/logout')
def logout(response: Response):
    response.delete_cookie('dental_session', path='/')
    return {'ok': True}


@app.get('/api/me')
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return user_payload(db, user)


@app.get('/api/admin/catalog')
def access_catalog(db: Session = Depends(get_db), user: User = Depends(current_user)):
    admin_only(db, user)
    return {'modules': [m for m in MODULES if m not in ('users', 'audit')],
            'roles': sorted(ROLES),
            'role_defaults': {role: {module: default_access(role, module)
                        for module in MODULES} for role in sorted(ROLES)}}


@app.get('/api/admin/users')
def admin_users(db: Session = Depends(get_db), user: User = Depends(current_user)):
    admin_only(db, user)
    result = []
    for target in db.scalars(select(User).order_by(User.id.asc())):
        item = user_payload(db, target)
        item['created_at'] = target.created_at.isoformat() if target.created_at else ''
        item['overrides'] = {x.module: x.access for x in db.scalars(
            select(UserPermission).where(UserPermission.user_id == target.id))}
        result.append(item)
    return result


@app.post('/api/admin/users/{user_id}/review')
def admin_review_user(user_id: int, body: ReviewUserIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    admin_only(db, user)
    target = get_or_404(db, User, user_id)
    if target.id == user.id:
        raise HTTPException(409, 'You cannot change your own role or account status')
    target.role = body.role
    target.status = body.status
    target.session_epoch += 1
    # Overrides remain in place on role changes, so the admin can explicitly reset them.
    audit(db, user, 'ACCESS', target, f'Role={body.role}; status={body.status}; sessions revoked')
    db.commit()
    return user_payload(db, target)


@app.post('/api/admin/users/{user_id}/permission')
def admin_permission(user_id: int, body: UserPermissionIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    admin_only(db, user)
    target = get_or_404(db, User, user_id)
    if target.role == 'admin' or target.id == user.id:
        raise HTTPException(409, 'Administrator permissions are managed by the protected administrator role')
    if body.module not in MODULES or body.module in ('audit', 'users'):
        raise HTTPException(422, 'Unknown or administrator-only module')
    current = db.scalar(select(UserPermission).where(UserPermission.user_id == target.id,
                         UserPermission.module == body.module))
    if body.access == 'default':
        if current: db.delete(current)
    elif current:
        current.access = body.access
    else:
        db.add(UserPermission(user_id=target.id, module=body.module, access=body.access))
    target.session_epoch += 1
    audit(db, user, 'ACCESS', target, f'{body.module}={body.access}; sessions revoked')
    db.commit()
    return user_payload(db, target)


@app.get('/api/summary')
def summary(db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'dashboard', 'view')
    rights = permissions_for(db, user)
    def count(module, model):
        return (db.scalar(select(func.count()).select_from(model)) or 0) if rights[module]['view'] else None
    return {
        'patients': count('patients', Patient), 'appointments': count('appointments', Appointment),
        'care_plans': count('care-plans', CarePlan), 'procedures': count('procedures', Procedure),
        'trials': count('trials', Trial), 'enrollments': count('enrollments', Enrollment),
        'open_safety': (db.scalar(select(func.count()).select_from(SafetyEvent).where(SafetyEvent.status != 'CLOSED')) or 0) if rights['safety-events']['view'] else None,
        'stock_alerts': sum(1 for x in db.scalars(select(Stock)) if x.quantity <= x.reorder_point) if rights['stock']['view'] else None,
        'open_plans': (db.scalar(select(func.count()).select_from(CarePlan).where(CarePlan.status.in_(['APPROVED','IN_PROGRESS']))) or 0) if rights['care-plans']['view'] else None,
    }


@app.get('/api/{resource}')
def list_resource(resource: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    model = TABLES.get(resource)
    if not model:
        raise HTTPException(404)
    authorize(db, user, resource, 'view')
    items = db.scalars(select(model).order_by(model.id.desc()).limit(500)).all()
    return [as_dict(item) for item in items]


@app.post('/api/patients')
def new_patient(body: PatientIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'patients')
    parse_date(body.dob, 'birth date')
    if date.fromisoformat(body.dob) > date.today():
        raise HTTPException(422, 'Birth date cannot be in the future')
    # MRN is not based on a person's name and is allocated by the database ID.
    patient = Patient(mrn=f'TEMP-{secrets.token_hex(5)}', **body.model_dump())
    db.add(patient)
    db.flush()
    patient.mrn = f'DRC-{patient.id:05d}'
    audit(db, user, 'CREATE', patient, 'New patient registered')
    db.commit()
    db.refresh(patient)
    return as_dict(patient)


@app.post('/api/encounters')
def new_encounter(body: EncounterIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'encounters')
    validate_patient(db, body.patient_id)
    parse_date(body.seen_on)
    return save(db, user, Encounter(**body.model_dump()))


@app.post('/api/findings')
def new_finding(body: FindingIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'findings')
    validate_patient(db, body.patient_id)
    valid_tooth(body.tooth, optional=False)
    return save(db, user, Finding(**body.model_dump()))


@app.post('/api/care-plans')
def new_plan(body: PlanIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'care-plans')
    validate_patient(db, body.patient_id)
    valid_tooth(body.tooth)
    if body.trial_id is not None:
        trial = get_or_404(db, Trial, body.trial_id)
        if trial.status != 'ACTIVE' or not (enrollment := enrolled(db, body.patient_id, trial.id)) or enrollment.status != 'ACTIVE' or not active_consent(db, body.patient_id, trial.id):
            raise HTTPException(409, 'Research-linked treatment requires active study, enrollment and current documented consent')
    return save(db, user, CarePlan(**body.model_dump()), 'Proposed treatment; not yet approved')


@app.post('/api/care-plans/{plan_id}/status')
def plan_status(plan_id: int, body: StatusIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'care-plans')
    plan = get_or_404(db, CarePlan, plan_id)
    allowed = {'DRAFT': {'APPROVED', 'CANCELLED'}, 'APPROVED': {'IN_PROGRESS', 'CANCELLED'},
               'IN_PROGRESS': {'COMPLETED', 'CANCELLED'}, 'COMPLETED': set(), 'CANCELLED': set()}
    if body.status not in allowed[plan.status]:
        raise HTTPException(409, f'Cannot move care plan from {plan.status} to {body.status}')
    if body.status == 'COMPLETED' and not db.scalar(select(Procedure.id).where(Procedure.plan_id == plan.id).limit(1)):
        raise HTTPException(409, 'Record at least one performed procedure before completing the care plan')
    plan.status = body.status
    audit(db, user, 'STATUS', plan, body.status)
    db.commit()
    return as_dict(plan)


@app.post('/api/appointments')
def new_appointment(body: AppointmentIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'appointments')
    validate_patient(db, body.patient_id)
    try:
        datetime.fromisoformat(body.scheduled_at)
    except ValueError:
        raise HTTPException(422, 'Invalid appointment date/time')
    return save(db, user, Appointment(**body.model_dump()))


@app.post('/api/appointments/{appointment_id}/status')
def appointment_status(appointment_id: int, body: StatusIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'appointments')
    appointment = get_or_404(db, Appointment, appointment_id)
    if body.status not in {'Scheduled', 'Checked in', 'Completed', 'Cancelled', 'No show'}:
        raise HTTPException(422, 'Invalid appointment status')
    appointment.status = body.status
    audit(db, user, 'STATUS', appointment, body.status)
    db.commit()
    return as_dict(appointment)


@app.post('/api/procedures')
def new_procedure(body: ProcedureIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'procedures')
    plan = get_or_404(db, CarePlan, body.plan_id)
    if plan.patient_id != body.patient_id:
        raise HTTPException(409, 'Treatment plan and procedure patient must match')
    if plan.status not in {'APPROVED', 'IN_PROGRESS'}:
        raise HTTPException(409, 'Approve the care plan before documenting its procedure')
    if plan.trial_id is not None and not active_consent(db, plan.patient_id, plan.trial_id):
        raise HTTPException(409, 'Research consent withdrawn; research-linked procedure is blocked')
    parse_date(body.performed_on)
    if body.follow_up_on: parse_date(body.follow_up_on)
    obj = Procedure(**body.model_dump())
    db.add(obj)
    db.flush()
    if plan.status == 'APPROVED':
        plan.status = 'IN_PROGRESS'
        audit(db, user, 'STATUS', plan, 'IN_PROGRESS after procedure')
    audit(db, user, 'CREATE', obj, 'Procedure documented against approved plan')
    db.commit()
    db.refresh(obj)
    return as_dict(obj)


@app.post('/api/imaging')
def new_image(body: ImagingIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'imaging')
    validate_patient(db, body.patient_id)
    valid_tooth(body.tooth)
    parse_date(body.captured_on)
    return save(db, user, Imaging(**body.model_dump()), 'Image metadata only, no image file stored')


@app.post('/api/lab-orders')
def new_lab(body: LabIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'lab-orders')
    plan = get_or_404(db, CarePlan, body.plan_id)
    if plan.patient_id != body.patient_id: raise HTTPException(409, 'Plan and patient mismatch')
    parse_date(body.due_on)
    return save(db, user, LabOrder(**body.model_dump()))


@app.post('/api/invoices')
def new_invoice(body: InvoiceIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'invoices')
    validate_patient(db, body.patient_id)
    if body.plan_id:
        plan = get_or_404(db, CarePlan, body.plan_id)
        if plan.patient_id != body.patient_id: raise HTTPException(409, 'Plan and patient mismatch')
    if body.paid > body.amount: raise HTTPException(422, 'Paid cannot exceed amount')
    parse_date(body.created_on)
    return save(db, user, Invoice(**body.model_dump()))


@app.post('/api/invoices/{invoice_id}/pay')
def pay_invoice(invoice_id: int, body: PaymentIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'invoices')
    invoice = get_or_404(db, Invoice, invoice_id)
    if round(invoice.paid + body.amount, 2) > round(invoice.amount, 2):
        raise HTTPException(409, 'Payment exceeds outstanding balance')
    invoice.paid = round(invoice.paid + body.amount, 2)
    audit(db, user, 'PAYMENT', invoice, f'Recorded {body.amount:.2f}')
    db.commit()
    return as_dict(invoice)


@app.post('/api/stock')
def new_stock(body: StockIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'stock')
    if body.expiry: parse_date(body.expiry)
    return save(db, user, Stock(**body.model_dump()))


@app.post('/api/stock/{stock_id}/use')
def use_stock(stock_id: int, body: StockUseIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'stock')
    item = get_or_404(db, Stock, stock_id)
    if item.quantity < body.amount: raise HTTPException(409, 'Not enough stock')
    item.quantity = round(item.quantity - body.amount, 3)
    audit(db, user, 'DISPENSE', item, f'{body.amount} {item.unit}: {body.purpose}')
    db.commit()
    return as_dict(item)


@app.post('/api/trials')
def new_trial(body: TrialIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'trials')
    return save(db, user, Trial(**body.model_dump()), 'Protocol created; not authorized to recruit')


@app.post('/api/trials/{trial_id}/status')
def trial_status(trial_id: int, body: TrialApprovalIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    admin_only(db, user)
    trial = get_or_404(db, Trial, trial_id)
    allowed = {'DRAFT': {'EC_APPROVED'}, 'EC_APPROVED': {'ACTIVE', 'DRAFT'}, 'ACTIVE': {'CLOSED'}, 'CLOSED': set()}
    if body.status not in allowed[trial.status]:
        raise HTTPException(409, f'Invalid trial transition {trial.status} → {body.status}')
    for field in ('ec_reference', 'registry_reference', 'regulatory_reference'):
        if getattr(body, field).strip(): setattr(trial, field, getattr(body, field).strip())
    if body.status in {'EC_APPROVED', 'ACTIVE'} and not trial.ec_reference.strip():
        raise HTTPException(409, 'Document externally obtained Ethics Committee approval reference')
    if body.status == 'ACTIVE':
        if not trial.registry_reference.strip():
            raise HTTPException(409, 'Prospective trial registry reference required')
        if trial.regulatory_required and not trial.regulatory_reference.strip():
            raise HTTPException(409, 'Applicable regulatory authorization reference required')
    trial.status = body.status
    audit(db, user, 'STATUS', trial, f'{body.status}; references are metadata only, not independently verified')
    db.commit()
    return as_dict(trial)


@app.post('/api/consents')
def new_consent(body: ConsentIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'consents')
    validate_patient(db, body.patient_id)
    trial = get_or_404(db, Trial, body.trial_id)
    if trial.status != 'ACTIVE': raise HTTPException(409, 'Trial must be active to document participation consent')
    if not body.verified or not body.document_reference.strip():
        raise HTTPException(422, 'Confirm and reference a signed consent documented outside the system')
    parse_date(body.signed_on)
    if active_consent(db, body.patient_id, body.trial_id):
        raise HTTPException(409, 'Active consent already recorded for this participant and study')
    return save(db, user, Consent(**body.model_dump()), 'Metadata for externally signed consent; not an e-signature')


@app.post('/api/consents/{consent_id}/withdraw')
def withdraw_consent(consent_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'consents')
    consent = get_or_404(db, Consent, consent_id)
    if consent.withdrawn: raise HTTPException(409, 'Consent already withdrawn')
    consent.withdrawn = True
    current = enrolled(db, consent.patient_id, consent.trial_id)
    if current and current.status == 'ACTIVE':
        current.status = 'WITHDRAWN'
        audit(db, user, 'STATUS', current, 'Withdrawn after consent withdrawal')
    audit(db, user, 'WITHDRAW', consent, 'Participation consent withdrawn')
    db.commit()
    return as_dict(consent)


@app.post('/api/screenings')
def new_screening(body: ScreeningIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'screenings')
    trial = get_or_404(db, Trial, body.trial_id)
    validate_patient(db, body.patient_id)
    if trial.status != 'ACTIVE': raise HTTPException(409, 'Trial is not active')
    if not active_consent(db, body.patient_id, trial.id):
        raise HTTPException(409, 'Document consent before performing protocol-specific screening')
    if body.eligibility not in {'PENDING', 'ELIGIBLE', 'INELIGIBLE'}:
        raise HTTPException(422, 'Eligibility must be PENDING, ELIGIBLE or INELIGIBLE')
    if parse_date(body.screened_on) < date.fromisoformat(active_consent(db, body.patient_id, trial.id).signed_on):
        raise HTTPException(409, 'Screening cannot predate documented consent')
    return save(db, user, Screening(**body.model_dump()), 'Human reviewer determines criteria; system does not decide eligibility')


@app.post('/api/enrollments')
def new_enrollment(body: EnrollmentIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'enrollments')
    trial = get_or_404(db, Trial, body.trial_id)
    validate_patient(db, body.patient_id)
    if trial.status != 'ACTIVE': raise HTTPException(409, 'Study must be active')
    consent = active_consent(db, body.patient_id, body.trial_id)
    if not consent: raise HTTPException(409, 'Current documented informed consent is required')
    if date.fromisoformat(consent.signed_on) > parse_date(body.enrolled_on):
        raise HTTPException(409, 'Consent date must not be later than enrollment date')
    screening = db.scalars(select(Screening).where(Screening.patient_id == body.patient_id,
                    Screening.trial_id == body.trial_id).order_by(Screening.id.desc())).first()
    if not screening or screening.eligibility != 'ELIGIBLE':
        raise HTTPException(409, 'The latest completed screening must show ELIGIBLE')
    if parse_date(screening.screened_on) > date.fromisoformat(body.enrolled_on):
        raise HTTPException(409, 'Enrollment cannot precede eligibility screening')
    if enrolled(db, body.patient_id, body.trial_id): raise HTTPException(409, 'Already enrolled in this trial')
    n = db.scalar(select(func.count()).select_from(Enrollment).where(Enrollment.trial_id == trial.id)) or 0
    code = f'{trial.code}-S{n + 1:03d}'
    return save(db, user, Enrollment(**body.model_dump(), subject_code=code), 'Study-specific subject ID allocated')


@app.post('/api/research-visits')
def new_research_visit(body: ResearchVisitIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'research-visits')
    enrollment = get_or_404(db, Enrollment, body.enrollment_id)
    if enrollment.status != 'ACTIVE' or not active_consent(db, enrollment.patient_id, enrollment.trial_id):
        raise HTTPException(409, 'Research visit requires active enrolled participant with current consent')
    if get_or_404(db, Trial, enrollment.trial_id).status != 'ACTIVE':
        raise HTTPException(409, 'Study is not active')
    parse_date(body.visit_on)
    return save(db, user, ResearchVisit(**body.model_dump()), 'Protocol visit with dental endpoints')


@app.post('/api/safety-events')
def new_safety_event(body: SafetyIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'safety-events')
    enrollment = get_or_404(db, Enrollment, body.enrollment_id)
    parse_date(body.onset_on)
    obj = SafetyEvent(**body.model_dump())
    return save(db, user, obj, 'SERIOUS: prompt investigator review/reporting assessment' if obj.serious else 'AE recorded')


@app.post('/api/safety-events/{event_id}/status')
def safety_status(event_id: int, body: SafetyUpdateIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    authorize(db, user, 'safety-events')
    event = get_or_404(db, SafetyEvent, event_id)
    if body.status not in {'OPEN', 'UNDER_REVIEW', 'REPORTED', 'CLOSED'}:
        raise HTTPException(422, 'Invalid safety status')
    if event.serious and body.status in {'REPORTED', 'CLOSED'} and not body.reported_on:
        raise HTTPException(409, 'Record external safety report date for serious event')
    if body.reported_on: parse_date(body.reported_on)
    event.status = body.status
    event.reported_on = body.reported_on or event.reported_on
    event.outcome = body.outcome
    audit(db, user, 'STATUS', event, f'{body.status} - {body.outcome}')
    db.commit()
    return as_dict(event)


def seed_demo(db: Session):
    """Fictional seed; never use these passwords or data in production."""
    for username, role, display in [
        ('admin', 'admin', 'Centre Administrator'), ('dentist', 'dentist', 'Dr. A. Mehta'),
        ('researcher', 'researcher', 'Research Investigator'), ('coordinator', 'coordinator', 'Study Coordinator'),
        ('frontdesk', 'receptionist', 'Front Desk')]:
        db.add(User(username=username, role=role, requested_role=role, status='ACTIVE', display_name=display, pw_hash=hash_password(os.getenv('DEMO_PASSWORD', 'Demo@12345'))))
    db.flush()
    p1 = Patient(mrn='DRC-00001', name='Ananya Sharma (Demo)', dob='1996-04-18', gender='Female', phone='0000000001',
                 allergies='None reported', medical_history='Fictional teaching record', medical_alerts='Check medication history')
    p2 = Patient(mrn='DRC-00002', name='Rahul Verma (Demo)', dob='1988-11-03', gender='Male', phone='0000000002',
                 allergies='Penicillin reported', medical_history='Fictional teaching record')
    p3 = Patient(mrn='DRC-00003', name='Meera Singh (Demo)', dob='1979-02-22', gender='Female', phone='0000000003',
                 allergies='None reported', medical_history='Fictional teaching record')
    db.add_all([p1, p2, p3]); db.flush()
    db.add_all([
        Encounter(patient_id=p1.id, seen_on='2026-10-19', dentist='Dr. A. Mehta', complaint='Sensitivity in lower molar', diagnosis='Dental caries', clinical_notes='Example chart entry'),
        Encounter(patient_id=p2.id, seen_on='2026-10-20', dentist='Dr. A. Mehta', complaint='Persistent tooth pain', diagnosis='Pulpitis', clinical_notes='Example chart entry'),
        Encounter(patient_id=p3.id, seen_on='2026-10-20', dentist='Dr. A. Mehta', complaint='Gum bleeding', diagnosis='Periodontal inflammation', clinical_notes='Example chart entry'),
        Finding(patient_id=p1.id, tooth='36', surface='Occlusal', finding='Caries', severity='Moderate', notes='Teaching example'),
        Finding(patient_id=p2.id, tooth='16', surface='All', finding='Pulpitis', severity='Severe', notes='Teaching example'),
        Finding(patient_id=p3.id, tooth='31', surface='All', finding='Periodontal pocket', severity='Moderate', probing_mm=5, bleeding=True),
    ])
    trial = Trial(code='DENT-PERIO-001', title='Demo periodontal therapy outcomes study', indication='Periodontal disease',
        intervention='Standard dental cleaning comparison (illustrative only)', design='Interventional',
        primary_endpoint='Change in probing depth at Week 8', status='ACTIVE',
        ec_reference='DEMO-EC-NOT-REAL', registry_reference='DEMO-REG-NOT-REAL', regulatory_required=False)
    db.add(trial); db.flush()
    plan1 = CarePlan(patient_id=p1.id, tooth='36', diagnosis='Caries', procedure='Composite restoration',
        sequence='Definitive care', priority='Routine', estimated_cost=2600, status='APPROVED')
    plan2 = CarePlan(patient_id=p2.id, tooth='16', diagnosis='Pulpitis', procedure='Root canal treatment',
        sequence='Definitive care', priority='Urgent', estimated_cost=8500, status='IN_PROGRESS')
    plan3 = CarePlan(patient_id=p3.id, tooth='31', diagnosis='Periodontal inflammation', procedure='Scaling and root planing',
        sequence='Disease control', priority='Routine', estimated_cost=4800, status='IN_PROGRESS', trial_id=trial.id)
    db.add_all([plan1, plan2, plan3]); db.flush()
    consent = Consent(patient_id=p3.id, trial_id=trial.id, document_version='v1.0', signed_on='2026-10-10',
        obtained_by='Demo Research Investigator', document_reference='DEMO-ICF-NOT-REAL', verified=True)
    db.add(consent)
    db.add(Screening(patient_id=p3.id, trial_id=trial.id, screened_on='2026-10-11', eligibility='ELIGIBLE',
        inclusion_exclusion_notes='Fictional eligibility review; not a real clinical assessment', reviewer='Demo Research Investigator'))
    db.add(Enrollment(patient_id=p3.id, trial_id=trial.id, subject_code='DENT-PERIO-001-S001', enrolled_on='2026-10-12'))
    db.flush()
    enroll = db.scalar(select(Enrollment).where(Enrollment.patient_id == p3.id))
    db.add_all([
        Appointment(patient_id=p1.id, scheduled_at='2026-10-26T10:30', provider='Dr. A. Mehta', purpose='Restoration', notes='Dental room 2'),
        Appointment(patient_id=p2.id, scheduled_at='2026-10-26T12:00', provider='Dr. A. Mehta', purpose='Endodontic follow-up'),
        Appointment(patient_id=p3.id, scheduled_at='2026-10-28T11:00', provider='Dr. A. Mehta', purpose='Periodontal review'),
        Procedure(patient_id=p2.id, plan_id=plan2.id, performed_on='2026-10-20', clinician='Dr. A. Mehta',
                  performed='Root canal - first visit', outcome='In progress', instructions='Fictional example only', follow_up_on='2026-10-26'),
        Procedure(patient_id=p3.id, plan_id=plan3.id, performed_on='2026-10-20', clinician='Dr. A. Mehta',
                  performed='Scaling and root planing', outcome='Completed', instructions='Fictional example only', follow_up_on='2026-10-28'),
        Imaging(patient_id=p2.id, modality='Periapical X-ray', tooth='16', captured_on='2026-10-19',
                reference='DEMO-RAD-001', impression='Educational placeholder — no image is stored'),
        LabOrder(patient_id=p2.id, plan_id=plan2.id, work_type='Zirconia crown', laboratory='Demo Dental Lab', due_on='2026-11-04', shade='A2'),
        Invoice(patient_id=p1.id, plan_id=plan1.id, description='Composite restoration estimate', amount=2600, paid=1000, created_on='2026-10-19'),
        Invoice(patient_id=p2.id, plan_id=plan2.id, description='Root canal treatment', amount=8500, paid=4000, created_on='2026-10-20'),
        Stock(name='Composite resin A2', category='Restorative', batch='DEMO-B001', quantity=4, reorder_point=5, unit='packs', expiry='2027-12-31'),
        Stock(name='Dental gloves', category='Consumables', batch='DEMO-G002', quantity=96, reorder_point=20, unit='boxes', expiry='2027-05-10'),
        ResearchVisit(enrollment_id=enroll.id, visit_name='Baseline', visit_on='2026-10-12',
                      probing_mm=5.0, plaque_index=2.0, bleeding_pct=42, dmft=6, pain_score=3, notes='Synthetic trial example'),
        SafetyEvent(enrollment_id=enroll.id, onset_on='2026-10-21', description='Mild gum discomfort after cleaning (demo)',
                    serious=False, severity='Mild', relatedness='Possible', status='OPEN', outcome='Recovering'),
        Audit(actor='SYSTEM', action='SEED', entity='patients', entity_id=p1.id, detail='Fictional demo environment initialized'),
    ])
    db.commit()
