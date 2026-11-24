# Engineering Decision Log

**Project:** Campus Walkie-Talkie Channel and Time-Slot Allocation Engine  
**Team:** E037 · **Project code:** ECE-018  
**Team members:** Surya Prakash.S and Sudarshan V.

This log records material engineering decisions reflected in the current project specification and implementation. It does not claim to reproduce undocumented meeting discussions.

| ID | Decision | Rationale | Evidence |
|---|---|---|---|
| DL-001 | Deliver a software scheduling simulation; do not control physical radio hardware. | Keep scope focused on campus channel and time-slot allocation. | Project specification and README. |
| DL-002 | Separate Flask routes, application services and a framework-independent allocation engine. | Keep web workflows separate from reusable allocation logic. | `app/routes.py`, `app/services/allocation_engine.py`, `app/services/command_runner.py`. |
| DL-003 | Use Python, Flask, HTML, CSS and JavaScript. | Provide a browser-based application with a Python backend. | Application source and dependencies. |
| DL-004 | Use SQLAlchemy; SQLite is the default local preview database and MySQL is supported through configuration. | Allow zero-configuration local setup while supporting MySQL. Database switching does not automatically migrate existing data. | `config.py`, `app/models.py`, `docs/ARCHITECTURE.md`. |
| DL-005 | Configure 16 channels; allocate only channels 1–15. Channel 16 is permanently reserved, including for emergency requests. | Protect the reserved channel from allocation. | Specification, allocation engine and model constraints. |
| DL-006 | Use 48 daily slots of 30 minutes each, with inclusive slot boundaries. | Provide deterministic half-hour scheduling. | Specification and allocation tests. |
| DL-007 | Prevent different groups from using the same or adjacent channels in the same slot; same-group adjacency is allowed. | Apply the defined cross-group separation rule. | Specification and allocation engine. |
| DL-008 | Apply priority order SECURITY, MEDICAL, EVENTS, MAINTENANCE; use FIFO within each category. | Make priority handling deterministic. | Specification and allocation engine. |
| DL-009 | Merge overlapping same-group requests before initial allocation, using the maximum channel demand rather than summing demand. | Avoid double-counting overlapping demand. | Specification and merge implementation. |
| DL-010 | Allocate a request atomically across its complete interval and channel demand. | Avoid partial allocations. | Allocation engine and automated tests. |
| DL-011 | For automatic requests, preserve valid channel continuity and then choose the lowest valid channel numbers. Fixed-channel requests use their exact channel list. | Keep allocation deterministic and stable. | Allocation engine and tests. |
| DL-012 | Permit pre-emption only for late requests after the date's allocation run; remove a whole lower-priority victim only when the complete late request then fits. | Limit disruption and follow the specified late-arrival policy. | Specification and allocation engine. |
| DL-013 | Use ADMIN and GROUP_USER application roles. | Separate administration from group-level workflows. | Models and route authorization. |
| DL-014 | Store password hashes, not plaintext passwords. | Avoid retaining raw credentials. | User model password hashing. |
| DL-015 | Preserve official command syntax, CSV names, column order and conflict reason codes. | Maintain compatibility with the E037 evaluation input/output contract. | Command runner and tests. |
| DL-016 | Use database uniqueness and check constraints to guard allocation records. | Add persistence-level protection against duplicate or invalid allocations. | `app/models.py`. |

## Maintenance notes

- Add a new entry when a material decision changes; reference any superseded decision.
- Record alternatives, owner and date for future decisions where known.
- Test evidence belongs in [the verification report](VERIFICATION_REPORT.md), not in this decision log.
