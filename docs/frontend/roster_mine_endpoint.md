# Self-Scoped Roster Endpoint — `GET /shifts/mine/`

Lets every active staff member fetch **their own** weekly shifts without
requiring manager-tier `attendance.shift.read`.

---

## URL

```
GET /api/hotel/<hotel_slug>/attendance/shifts/mine/
```

URL name: `attendance:staff-roster-mine` ([attendance/urls.py:131](attendance/urls.py#L131)).

## Auth

Standard staff Token in `Authorization: Token <token>` header (same as
all other `/attendance/` endpoints).

## RBAC

Permission stack on the action ([attendance/views.py:1717-1731](attendance/views.py#L1717-L1731)):

```
IsAuthenticated
CanViewAttendanceModule        → attendance.module.view
IsStaffMember
IsSameHotel
CanReadOwnRoster               → attendance.roster.read_self
```

`attendance.roster.read_self` is part of `_ATTENDANCE_SELF_SERVICE` and
is granted to **every** tier (`regular_staff`, `staff_admin`,
`super_staff_admin`), so any active same-hotel staff can call it.

## Query params (all optional)

| Param    | Format       | Effect                                  |
|----------|--------------|-----------------------------------------|
| `start`  | `YYYY-MM-DD` | Lower bound on `shift_date` (paired)    |
| `end`    | `YYYY-MM-DD` | Upper bound on `shift_date` (paired)    |
| `period` | integer      | Filter to a specific `RosterPeriod` id  |

The view force-filters `staff = request.user.staff_profile` and
`hotel = <URL hotel>` server-side — clients cannot widen the scope.

## Response

`200 OK` — JSON array of shifts (no pagination), shape from
`StaffRosterSerializer`. Ordered by `shift_date`, `shift_start`.

## Errors

| Status | Cause                                                      |
|--------|------------------------------------------------------------|
| 401    | Missing / invalid token                                    |
| 403    | User has no `staff_profile`, or hotel mismatch, or missing `attendance.module.view` / `attendance.roster.read_self` |
| 404    | Unknown `hotel_slug`                                       |

## Frontend usage

```ts
const params = new URLSearchParams({ start, end });
const res = await api.get(
  `/api/hotel/${hotelSlug}/attendance/shifts/mine/?${params}`
);
return res.data; // StaffRoster[]
```

### When to use vs the manager route

```ts
const canSeeAllShifts = !!rbac?.attendance?.actions?.shift_read;

const url = canSeeAllShifts
  ? `/api/hotel/${slug}/attendance/shifts/?staff=${myId}&start=${s}&end=${e}`
  : `/api/hotel/${slug}/attendance/shifts/mine/?start=${s}&end=${e}`;
```

- `shift_read = true` → manager / editor; use `/shifts/?staff=…` for
  full filter surface (cross-staff, by department, etc.).
- `shift_read = false` → regular staff; call `/shifts/mine/`.
