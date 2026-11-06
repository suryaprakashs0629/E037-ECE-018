# Website navigation and page guide

## Public page

| Route | Purpose |
|---|---|
| `/login` | Local account sign-in |
| `/health` | Application status |
| `/health/db` | Database connectivity |

## Administrator navigation

| Navigation group | Page | Route | Main operations |
|---|---|---|---|
| Workspace | Overview | `/dashboard` | System metrics, utilisation, recent audit activity, shortcuts |
| Operations | Request management | `/requests` | Search/filter, approve, reject, edit pending/approved request, cancel request |
| Operations | Allocation runs | `/admin/allocation-runs` | Run date allocation and inspect run history |
| Operations | Allocation schedule | `/schedule` | 48-slot by 16-channel timetable and group filter |
| Operations | Channel plan | `/admin/channels` | Inspect all channels and reserved channel 16 |
| Directory | Groups | `/admin/groups` | Create, edit and deactivate/activate groups |
| Directory | User accounts | `/admin/users` | Create, edit, reset password, authorise emergency requests, deactivate users |
| Oversight | Conflict log | `/admin/conflicts` | Inspect rejected, merged and pre-empted requests |
| Oversight | Reports | `/reports` | Date-based utilisation, statuses, category mix, official CSV export |
| Oversight | Command file lab | `/admin/command-center` | Run bundled official pack or upload the original three files |
| Oversight | Audit trail | `/admin/audit` | Read administrative and system events |
| Personal | Notifications | `/admin/notifications` | Read and mark notifications |
| Personal | Account settings | `/profile` | View account and change password |

## Group-user navigation

| Navigation group | Page | Route | Main operations |
|---|---|---|---|
| Workspace | My dashboard | `/dashboard` | Own request statuses, upcoming requests and notifications |
| My radio access | My requests | `/requests` | View own-group requests and edit pending requests |
| My radio access | Submit request | `/requests/new` | Create a channel request for assigned group |
| My radio access | My schedule | `/schedule` | View own group's committed channel assignments |
| Personal | Notifications | `/admin/notifications` | Read and mark notifications |
| Personal | Account settings | `/profile` | Change password |

Group data is scoped in database queries on the server, not only by hiding navigation links.
