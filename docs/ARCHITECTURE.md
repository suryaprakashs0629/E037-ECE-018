# Application architecture

## Separation of concerns

```text
Browser
  |
  +-- Administrator pages
  +-- Group-user pages
  +-- Command File Lab
          |
          v
     Flask routes (authentication, RBAC, form input)
          |
          v
     Application services
          |
          +-- Request validation and workflow
          +-- Official command parser / master data loader
          +-- Framework-independent allocation engine
          +-- CSV output writer and reports
          +-- Notifications and audit history
          |
          v
     SQLAlchemy persistence layer
          |
          +-- SQLite quick-preview database
          +-- MySQL Community Server for final/local project use
```

## Allocation engine components

```text
Request input
    |
    v
Validate group, slot range, duration, channel count and fixed channels
    |
    v
Initial ALLOCATE? ---- no ----> Late-arrival allocation path
    |                               |
   yes                              v
    |                         Try normal full allocation
    v                               |
Merge same-group overlaps           v
    |                         If blocked, inspect lower-priority victims
    v                               |
Sort category priority + FIFO       v
    |                         Remove one whole victim only if that makes
    v                         the complete late request fit
Try continuity-preserving channels |
    |                               |
    v                               v
Try lowest valid channels       Commit or NO_CHANNEL
    |
    v
Check same-channel and cross-group adjacency
    |
    v
Complete interval possible?
    | yes                 | no
    v                     v
Commit all rows        Discard all tentative rows; log first failed slot
```

## Data persistence

The web application stores account, group, channel, request, allocation, allocation-run, conflict, request-event, notification and audit records. The standalone command runner uses the same pure Python allocation engine and writes the official three CSV files. It does not require a web session or a MySQL connection.

## Database modes

- SQLite is the no-configuration local preview mode.
- MySQL is supported through `DATABASE_URL` and is the recommended database backend for the final ECE-018 application.
- Switching database backends creates/uses a separate database; it does not automatically migrate data from SQLite to MySQL.
