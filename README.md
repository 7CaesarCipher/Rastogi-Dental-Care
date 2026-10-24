# NOX Dental | Dental Hospital & Research Centre

A runnable, full-stack **dental care + dental research demonstration**. The FastAPI backend serves a responsive GUI and provides a REST API with an automatically seeded SQLite database; Docker Compose uses PostgreSQL.

**IMPORTANT:** This is a **prototype with entirely fictional example data**, not a production electronic health record, clinical-trial EDC, certified electronic consent/e-signature tool, or validated GxP system. Do not enter real personally identifiable patient information or use this software to direct real care, research enrollment, investigational treatment, or regulatory reporting.

## Start the application

### Option A — Mac or Linux (fastest: SQLite, no Docker)

```bash
cd dental_research_centre
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8087
```

Or double-click `run_mac.command` on a Mac, or run `bash run_linux.sh` on Linux.

### Option B — Windows (PowerShell or Command Prompt)

```powershell
cd dental_research_centre
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8087
```

Or run `run_windows.bat`. We invoke the environment's Python directly, so PowerShell `Activate.ps1` permissions are **not** a problem.

### Option C — Docker (PostgreSQL)

```bash
cd dental_research_centre
# Optional: in .env set SECRET_KEY to a long random value and APP_PORT=8087
docker compose up --build -d
# Logs and service status
docker compose ps
docker compose logs -f web
```

Open **http://localhost:8087** in your browser. The Swagger REST API reference is at **http://localhost:8087/docs**.

Default port is **8087** (chosen to avoid the common local port-8000 conflicts). With Docker, change the host port in `.env` (`APP_PORT=8095`); without Docker, change the number in the `uvicorn --port` argument. The SQLite database file is created automatically as `dental_demo.db` at the project root.

## Demo login

| Role | Username | Password |
|---|---|---|
| Administrator | `admin` | `Demo@12345` |
| Dentist | `dentist` | `Demo@12345` |
| Research investigator | `researcher` | `Demo@12345` |
| Research coordinator | `coordinator` | `Demo@12345` |
| Receptionist | `frontdesk` | `Demo@12345` |

All demo user accounts are created only when the database starts empty. **Never expose this demo instance or its credentials to a public network.**

## New in v2 — staff sign-up, personalized navigation and permission administration

**New staff sign-up:** On the login screen choose **Create a staff account**. Provide full name, username, requested role (Dentist / Researcher / Coordinator / Front desk), password and confirmation. Passwords require 12 or more characters including uppercase, lowercase and a number. New accounts are saved as `PENDING` and **cannot log in** until approved. Self-sign-up cannot request administrator privileges. This is staff registration—not patient portal enrollment.

**Administrator approval:** Sign in as `admin` and open **Administration → User permissions**. Review pending registrations, select an assigned role and select `ACTIVE`, or simply click **Approve & activate**. Choose `SUSPENDED` later to deny access. Administrators cannot change their own role/status using this page.

**Per-user module access:** Expand **Module permissions** for a user. For every non-administration module, choose **Role default**, **No access**, **View only** or **View & edit**. These overrides remain assigned to that user until reset, even if their role changes. The menu only shows modules the signed-in account may view, and the REST API enforces module-specific *read and write permissions* independently of the menu. A user with **View only** may list module records, but not create or update them. Study approval, the audit trail, and staff management are always protected administrator functions.

**Existing DB compatibility:** On startup, v2 performs a minimal additive schema update to existing v1 `users` tables and creates `user_permissions`. Existing demo accounts remain `ACTIVE` with their previous roles. Back up your database first. This is a demonstration migration; use a versioned migration system for production.

**Session behavior:** Changing a user’s role, permission or account status invalidates existing login sessions. The user must log in again to see their updated options. Sign-up and account updates are recorded in the demo audit log (not tamper-evident).

### Default module visibility

| Role | Main writable modules | Other selected view-only modules |
|---|---|---|
| Administrator | All | None (full access) |
| Dentist | Patients, encounters, chart, treatment plans, procedures, appointments, imaging, prosthetic lab, stock, AE entry | Trial protocols |
| Researcher | Trial protocols, consent, screening, enrollment, study visits, AE/SAE | Patients, encounters, chart, treatment plans, procedures, imaging |
| Coordinator | Appointments, consent, screening, enrollment, visits, AE/SAE | Patients, trial protocols |
| Front desk | Registration, appointments, billing | Dashboard |

The UI automatically adapts to further custom permissions granted by the administrator.

**Security limitation:** This demo does not implement email verification, password recovery, MFA, password rate limiting, tenant/clinic scoping, individual patient access rules, comprehensive audit integrity, production-grade authentication or encryption management. The initial administrator credentials are published demo credentials. Do **not** expose this instance publicly or upload real data.


## Implemented modules

| Clinical / dental | Clinical research | Operations |
|---|---|---|
| Registration and history | Protocol and EC / registry references | Role-based sign-in and staff sign-up |
| Clinical encounters and diagnoses | Consent-document verification | Scheduling and status |
| FDI tooth findings and periodontal measurements | Protocol-specific screening | Billing and payments |
| Phased treatment plans / clinician approval | Eligibility and subject enrollment | Dental material batches |
| Procedures matched to approved care plans | Dental endpoint eCRF visits | Stock usage and reorder alerts |
| Radiology and intraoral image **metadata** | AE/SAE documentation / review | Activity log |
| Prosthetic laboratory orders | Research-linked treatment | Dashboard |

Note: Imaging stores a **reference/path and clinical interpretation, not uploaded DICOM/JPG files**; lab orders currently have create/list but no status-change action. Study safety reporting is **record tracking only**, not an integrated regulatory gateway.

## Follow the two working processes

### 1. Dental care

1. Log in as `dentist` or `admin` and choose **Patients → Register patient**.
2. Add a **Dental encounter** with chief complaint, findings, diagnosis and clinical notes.
3. Choose **Dental chart**, select a patient and click an FDI tooth (e.g. `36`). Document caries, probing depth and/or bleeding.
4. Choose **Treatment plans** and create a diagnosis-linked plan (`Composite restoration`, `Root canal treatment`, `Scaling and root planing`, `Dental extraction`, `Crown`, `Implant`, etc.). Include phase, priority, estimated cost, and tooth.
5. Use **Approve** on the plan. A procedure **cannot** be documented until its plan is approved; treatment-plan/patient mismatches are blocked.
6. Create an **Appointment**, document the **Procedure**, add **Imaging** metadata or **Prosthetic lab** work when relevant, and set the plan to completed (completion requires a documented procedure).
7. Record an invoice/payment, and monitor materials. Plan follow-up or maintenance visits.

The sequencing labels are *Emergency care → Disease control → Definitive care → Rehabilitation → Maintenance/recall*, giving a single journey across multiple dental procedures.

### 2. Clinical trial / dental research

1. Log in as `researcher` or `admin`. Create a **Clinical trial** protocol with indication, design, intervention and primary endpoint.
2. Administrator records *external* **Ethics Committee approval** reference and changes `DRAFT → EC_APPROVED`. Before `ACTIVE`, a prospective trial registry reference is required, as well as regulator authorization where flagged applicable. The app **does not verify** these references against external authorities.
3. Research staff selects the candidate patient, conducts the actual informed-consent discussion **outside this app**, obtains the approved signed ICF, then records document version, date, staff and a secure document reference in **Informed consent**.
4. Document investigator-reviewed inclusion/exclusion criteria in **Screening**. Study-specific screening requires previously documented consent; the software **does not decide eligibility**.
5. Once the latest screening is `ELIGIBLE`, enroll. The app assigns a **trial-specific subject code** without exposing patient MRN in study visits.
6. Capture **Study visits / eCRF** measurements: mean probing depth, plaque index, bleeding percentage, DMFT and pain score.
7. A qualified clinician may link a treatment plan to an active trial *only when the patient is actively enrolled and has current documented consent*; treatment remains clinician-directed.
8. Create **AE / SAE safety** entries and move through review/reporting statuses. For a serious event, logging an external report date is required to mark `REPORTED` or `CLOSED`. Safety reporting **must** be handled separately per applicable rules.
9. Withdrawing recorded consent marks the active enrollment `WITHDRAWN` and blocks further protocol visits and research-linked dental procedures. The safety workflow remains available for necessary follow-up.

## Clinical process map

```text
PATIENT REGISTRATION ──> DENTAL ENCOUNTER ──> FDI CHART / PERIODONTAL RECORD
                                                 |
                                                 v
             FOLLOW-UP <── PROCEDURE <── APPROVED TREATMENT PLAN
                 |               |                 |
              OUTCOMES          LAB / IMAGE       ELIGIBLE FOR STUDY? (human review)
                                                        |
                                  PROTOCOL + EC / REGISTRY / APPLICABLE REGULATOR
                                                        |
                                             SIGNED ICF METADATA
                                                        |
                                       SCREENING → ENROLLMENT
                                                        |
                                     STUDY VISITS / DENTAL eCRF
                                                        |
                                       AE / SAE / RESEARCH OUTCOMES
```

**Participation is never required for routine dental treatment.** Research consent and clinical procedure consent are separate processes; the app only records metadata for research consent and does not implement clinical procedure consent capture.

## Tech stack and files

```text
dental_research_centre/
├── app/
│   ├── main.py                 FastAPI, SQLAlchemy models and workflow endpoints
│   └── static/
│       ├── index.html          Sign-in + responsive GUI
│       ├── app.css             UI design system
│       └── app.js              Dashboard, charts, forms, tables and actions
├── tests/test_workflows.py     Integration checks for workflow gates
├── docs/
│   ├── PRODUCT_REQUIREMENTS.md
│   └── CLINICAL_WORKFLOWS.md
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── run_mac.command
├── run_linux.sh
└── run_windows.bat
```

SQLite is installed automatically; PostgreSQL is used with Docker. `DATABASE_URL` chooses the database. For local development the default is SQLite; Docker Compose contains only the API and PostgreSQL services. The PostgreSQL database is not exposed to the host, so it should not conflict with other local Postgres ports.

## Tests

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

On Windows, replace `.venv/bin/python` with `.venv\Scripts\python.exe`.

## Research and privacy safeguards / things still needed for real clinical use

The prototype has checks for trial activation, consent before protocol screening, eligibility before enrollment, enrollment before research-linked treatment, dental procedure vs. plan, and consent withdrawal. It also tracks audit activity and applies user-role write restrictions. These are **not** sufficient to claim GxP, privacy-law, cybersecurity, medical-device, dental practice, or research-regulatory compliance.

Before real deployment: formal requirements validation and UAT; clinical/ethics oversight; privacy impact assessment and medical record retention policies; enforce per-user/patient/site read access; encrypted storage/backups and TLS; unique non-demo accounts, password reset and MFA; separate independently verifiable signed eConsent where allowed; tamper-evident audit and electronic signatures where necessary; protocol versioning, deviations and monitoring; restricted study randomization/IP accountability; verified source documents and imaging storage; adverse event reporting rules and clocks; system change control, computerized system validation, disaster recovery, controlled exports, audit and investigator approval workflows. Do **not** use this implementation with real patients.

## External guidance informing the illustrative process

- [CDSCO – Ethics Committee](https://cdsco.gov.in/opencms/opencms/en/Clinical-Trial/Ethics-Committee/)
- [New Drugs and Clinical Trials Rules, 2019 (CDSCO)](https://cdsco.gov.in/opencms/export/sites/CDSCO_WEB/Pdf-documents/IVD/Guideline-Documents/NEW-DRUGS-AND-CLINICAL-TRIALS-RULES-2019.pdf)
- [CTRI – Prospective registration FAQs](https://ctri.nic.in/Clinicaltrials/faq.php)
- [ICMR National Ethical Guidelines for Biomedical and Health Research Involving Human Participants, 2017](https://www.icmr.gov.in/icmrobject/custom_data/pdf/resource-guidelines/ICMR_Ethical_Guidelines_2017.pdf)
- [ICH E6(R3) Good Clinical Practice (EMA)](https://www.ema.europa.eu/en/scientific-guidelines/ich-e6-good-clinical-practice)

The legal applicability of specific authorizations and study registration depends on the study's jurisdiction, device/drug status, research design and protocol. Seek site-qualified legal, ethics, and quality advice before any real study.
