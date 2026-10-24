# Dental Hospital & Research Centre — Product Requirements

**Version:** Prototype v2.0 — 24 October 2026. **Audience:** Dental practice leads, clinical investigators, research coordinators, clinical IT.

## Vision

Create one patient-centered system where clinical examinations, sequential dental care, return appointments, and dental research can share an auditable reference to the same *eligible* patient without confusing ordinary care with voluntary study participation.

## Personas and permissions

| Persona | Core job | Demo authorized writes |
|---|---|---|
| Administrator | Manage workflows and study activation | All write operations |
| Dentist | Examine, chart, plan, treat, follow up | Clinical records, materials and safety event entry |
| Researcher | Develop protocols, assess study data | Trial creation; consent, screening, enrollment, visit and safety |
| Coordinator | Manage protocol participants and visits | Consent, screening, enrollment, visits, safety |
| Receptionist | Registration, appointments and billing | Patient, appointment and invoice/payment |

Effective access is **per user, per module**, with role defaults and administrator-managed overrides (`none`, `read`, `write`). Both read and write API endpoints enforce access; unpermitted navigation items are hidden. Administrator account management and audit access cannot be delegated to non-admin roles. Staff self-register but remain pending until an administrator activates them. Account changes revoke prior sessions. Production must additionally add patient-level and site-level access controls, e-mail verification, delegation logs, and least-privilege separation.

## Functional requirements (built)

| ID | Requirement | Module | Demonstration acceptance |
|---|---|---|---|
| D-01 | Create patient MRN and dental history | Patient | Unique MRN generated |
| D-02 | Capture clinical encounter / dentist diagnosis | Encounter | Encounter linked to patient |
| D-03 | Chart tooth using FDI notation and periodontal metrics | Chart | Invalid code rejected |
| D-04 | Treatment priority, phase, estimated cost and trial link | Care plan | Approval required before procedure |
| D-05 | Procedure date, operator, after-care, follow-up date | Procedures | Patient/plan mismatch blocked |
| D-06 | Schedule / update appointment | Appointments | State change saved |
| D-07 | X-ray and intraoral photo metadata | Imaging | Image reference saved; binary storage deferred |
| D-08 | Crown/denture appliance lab order | Lab | Plan-linked order saved |
| D-09 | Charge, payment, outstanding balance | Billing | Overpayment rejected |
| D-10 | Stock count, batch, expiry, reorder alert | Stock | Negative stock rejected |
| R-01 | Trial protocol, EC, registry and regulator references | Trial | Activation gates enforced |
| R-02 | Verified signed consent reference / withdrawal | Consent | Unsigned flag rejected |
| R-03 | Screening eligibility after consent | Screening | No protocol-screening without documented consent |
| R-04 | Enrollment and unique subject code | Participants | Eligible latest screen and consent required |
| R-05 | Oral/dental visit outcomes | eCRF | Bounds enforced on pain, DMFT and bleeding |
| R-06 | AE/SAE and external report date | Safety | Serious event cannot be marked reported without date |
| R-07 | Withdrawing consent prevents more visits | Study state | New research visit rejected |
| G-01 | Session auth, role defaults and per-user module permissions | Authentication | Non-permitted reads/writes receive HTTP 403 |
| G-02 | Date-stamped activity log | Audit | Create/status and access management events recorded |
| G-03 | Staff sign-up and approval | Login / Users | Self-registration is PENDING; administrator activates account |
| G-04 | Administrator role & permissions UI | Users | Admin controls role, account status and module read/write grants |
| G-05 | Session revocation | Security | Changed status, role or access invalidates existing cookie |
| G-06 | Protect account management & audit | Security | Admin-only, even if a different module is delegated |

## Scope by dental specialty

| Specialty | Examples supported at baseline | Later full clinical workflow |
|---|---|---|
| General / Restorative | Caries, examination, filling, preventive clean | Structured surfaces and restorative materials |
| Endodontics | Root canal treatment, pulpitis, periapical image | Canal mapping, obturation material and staged visits |
| Periodontics | Tooth pockets, bleeding, plaque / probing research outcomes | Full six-site periodontal chart, attachment loss, bleeding per site |
| Prosthodontics | Crowns, bridges, denture lab orders | Jaw relation, try-in, manufacturing case |
| Oral surgery | Extractions, implants, postoperative review | Surgical checklist, implant batch and detailed surgery note |
| Orthodontics | Treatment option, appointment, imaging reference | Cephalometric analysis, appliances, alignment milestones |
| Pediatric dentistry | Primary dentition FDI records and care plans | Age-specific risk screening, guardian consent and assent |
| Oral medicine / radiology | Lesion findings, X-ray metadata | Image/PACS integration, biopsies and pathology review |

## Nonfunctional and regulatory production requirements (future)

- Full GxP validation package (URS → functional/design specifications → risk-based testing → IQ/OQ/PQ as applicable), review, approvals, training and change control.
- Strong user enrollment, RBAC/ABAC for records, MFA, real account lifecycle and emergency/break-glass access.
- Immutable or tamper-evident audit records with before/after values, UTC event times, role, reason for change and signatures where required.
- Encryption in transit and at rest, backups, business continuity, data ownership, consent and retention/deletion protocols.
- Multi-site tenancy, authorized research dataset segmentation, ethics-controlled access to subjects and unblinding protections.
- Clinical procedure consent; prescription rules; clinical guidelines; decision-support governance and expert review.
- Validated randomization and investigational product handling where needed, pharmacy reconciliation, allocation concealment, medical coding, data queries, protocol deviations, SAE intake and regulatory reporting.
- Study design-specific controls: observational vs interventional, phase, device requirements, minors / vulnerable persons, jurisdiction, applicable regulator.
- Comprehensive quality/security assessment before integration with real EHR, laboratories, ePRO, PACS, EDC, Argus or other external systems.

## Suggested phases

**Phase 1 (included):** UI, demo database, dental treatment pathway, enrollment gates, dental research endpoints, staff sign-up, approval, module permissions and workflow tests.

**Phase 2:** Expanded tooth and periodontal charts, dental imaging uploads, procedural checklists, full appointment scheduling and controlled clinic billing.

**Phase 3:** Controlled eCRF templates, visit windows, data queries, deviation and monitoring logs, research supply accountability and audit/e-signature enhancements.

**Phase 4:** Formal CSV/GxP readiness, external regulatory integrations, tenant isolation, training, qualification and deployment operations.
