# Dental Treatment + Research Workflows

## A. Dental patient journey

| Workflow state | User | Action | Clinical output |
|---|---|---|---|
| Registered | Front desk | Demographics, alerts, history | Medical record number |
| Assessed | Dentist | History, pain, examination, imaging if relevant | Chief complaint / diagnosis |
| Charted | Dentist | FDI tooth, surfaces, periodontal pocket, BOP | Objective dental findings |
| Planned | Dentist | Care priority, tooth, phase, estimate | Treatment proposal |
| Approved | Dentist | Approve treatment plan | Allowed to record performed procedure |
| In progress | Dentist | Treatment, clinician, outcome, post-op instructions | Procedure note and follow-up |
| Completed | Dentist | Finish after at least one procedure note | Historical treatment plan |
| Maintenance | Front desk + dentist | Follow-up visit / periodontal reassessment | Longitudinal care |

**Note:** Real procedural consent, allergy/medication interaction decision support, detailed dental coding, emergency authorization and diagnostic verification are not implemented. Treatment is for qualified clinicians only.

## B. Clinical study participant journey

| Study state | Decision owner | Preconditions | Result |
|---|---|---|---|
| DRAFT | Research lead | Written protocol and design | Study created |
| EC_APPROVED | Administrator (recording external approval) | EC reference | Cannot enroll yet |
| ACTIVE | Administrator (recording external documentation) | EC and registry IDs, regulatory permission as applicable | Consent and screening available |
| Consented | Investigator / delegated staff | Actual informed-consent process and signed ICF | Verified consent metadata |
| Screened | Qualified trial team | Current consent; human criteria review | PENDING / ELIGIBLE / INELIGIBLE |
| Enrolled | Qualified trial team | Latest eligibility = ELIGIBLE, active consent | Unique study-specific subject code |
| Visited | Qualified trial team | Active enrollment and consent | Dental eCRF outcomes |
| Safety review | Clinical investigator | AE/SAE observation, seriousness assessment | Record and appropriate external reporting |
| Withdrawn | Participant / study team | Withdrawal of documented research consent | Study visit gate closes |
| CLOSED | Administrator | External study closeout authorized | New study visits blocked |

**Separation rule:** Treatment access is not dependent on study consent. Withdrawal of study consent does not imply discontinuation of medically appropriate clinical follow-up. Safety follow-up may still be legally/ethically required.

## C. Dental clinical research ideas

1. **Periodontal treatment:** scaling and root planing study; endpoint change in mean probing depth or bleeding percentage at Week 8.
2. **Restorative dentistry:** filling material comparative outcomes; endpoints restoration longevity, postoperative sensitivity and patient-reported pain.
3. **Endodontics:** root-canal techniques; follow-up endpoints pain, complications, healing according to approved protocol.
4. **Implantology:** implant stability / bone integration observations; carefully govern intervention, device traceability and adverse events.
5. **Orthodontics:** alignment techniques, comfort and treatment completion; account for guardian consent and assent for minors where relevant.
6. **Dental public health:** caries prevention, periodontal disease prevalence or fluoridation education; different research ethics and regulatory requirements by design.

These are study concepts, not approved protocols or treatment recommendations.

## D. Data model relationships

```text
patients (1) ── (N) encounters
patients (1) ── (N) findings
patients (1) ── (N) care_plans ── (N) procedures
                             └── (N) lab_orders
patients (1) ── (N) appointments, imaging, invoices
trials   (1) ── (N) consents ──────── (N) patients
trials   (1) ── (N) screenings ────── (N) patients
trials   (1) ── (N) enrollments ───── (N) patients
                          └── (N) research_visits
                          └── (N) safety_events
care_plans (N) ── (0..1) trials   [only active enrolled / consented]
```

All personal names, statuses, ICF IDs and approval numbers in default seed data are explicitly labeled demo/fictional.
