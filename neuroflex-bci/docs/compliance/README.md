# Compliance Documentation Templates

> **These documents are templates showing how a design-control file for a
> system like this would be organized. They are not evidence of, and do not
> claim, any actual regulatory clearance, certification, or audit.** No
> device built from this repository has been cleared by the FDA or any
> other regulator. Treat everything in this folder as a starting outline
> for a real quality management system (QMS), to be filled in, executed,
> and reviewed by qualified regulatory, quality, and clinical staff.

A real Class III active implantable neural-prosthetic system would need,
at minimum:

- A **Quality Management System** conforming to 21 CFR 820 / ISO 13485
- **Software lifecycle documentation** conforming to IEC 62304 (this
  software would very likely be Class C — failure could cause serious
  injury)
- A **Risk Management File** conforming to ISO 14971, including hazard
  analysis, risk controls, and verification that controls are effective
- **Design controls**: design inputs/outputs, verification, validation,
  traceability from requirements to test evidence
- **Usability engineering** file conforming to IEC 62366-1
- **Clinical evaluation** and, for a Class III device, a **Premarket
  Approval (PMA)** submission to FDA (or equivalent — e.g. EU MDR Class III
  route with a Notified Body)
- **Cybersecurity** documentation aligned with FDA's premarket
  cybersecurity guidance, given the wireless companion-app link
- **Biocompatibility** (ISO 10993) and **active implantable** standards
  (e.g. ISO 14708 series) evidence for the physical implant, which is
  entirely outside the scope of this software repository

## What's in this folder

| File | Maps to |
|---|---|
| [`IEC62304_MAPPING.md`](IEC62304_MAPPING.md) | Software safety classification and lifecycle process mapping |
| [`RISK_MANAGEMENT.md`](RISK_MANAGEMENT.md) | ISO 14971-style risk management summary (software-relevant subset) |
| [`CYBERSECURITY.md`](CYBERSECURITY.md) | Premarket cybersecurity considerations for the wireless/API surface |

These are intentionally scoped to what this software repository can speak
to. Hardware, biocompatibility, clinical, and manufacturing quality
records are out of scope here and would live in the broader company QMS.
