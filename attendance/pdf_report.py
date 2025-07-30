# attendance/pdf_report.py
from io import BytesIO
from datetime import datetime, date, time, timedelta
from collections import defaultdict

from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    ListFlowable, ListItem
)
from reportlab.lib.units import cm


# -------------------------- helpers -------------------------- #

def _to_time(value):
    """Supports 'HH:MM' or 'HH:MM:SS' or datetime.time."""
    if isinstance(value, time):
        return value
    parts = [int(p) for p in str(value).split(":")]
    if len(parts) == 2:
        parts.append(0)
    return time(*parts[:3])


def _hours_between(date_obj, start, end):
    dt_start = datetime.combine(date_obj, _to_time(start))
    dt_end = datetime.combine(date_obj, _to_time(end))
    return max((dt_end - dt_start).total_seconds() / 3600.0, 0.0)


def _fmt_hhmm(t):
    try:
        return str(t)[:5]
    except Exception:
        return str(t)


def _safe_staff_name(staff, staff_id=None):
    if not staff:
        return f"#{staff_id or ''}".strip()
    first = getattr(staff, "first_name", "") or ""
    last = getattr(staff, "last_name", "") or ""
    full = f"{first} {last}".strip()
    return full or f"#{getattr(staff, 'id', staff_id) or ''}"


# ------------------------------------------------------------- #
# 1) Your original flat list PDF (Daily / Staff range, etc.)
# ------------------------------------------------------------- #
def build_roster_pdf(title, meta_lines, shifts, landscape_mode=True):
    """
    Flat list PDF (Date, Staff, Start, End, Hours, Location).
    Reused for daily & per-staff exports.
    """
    buf = BytesIO()

    page_size = landscape(A4) if landscape_mode else portrait(A4)
    doc = SimpleDocTemplate(
        buf,
        pagesize=page_size,
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
    )

    styles = getSampleStyleSheet()
    elems = []

    # ---- header
    elems.append(Paragraph(title, styles["Title"]))
    for ml in meta_lines:
        elems.append(Paragraph(ml, styles["Normal"]))
    elems.append(Spacer(1, 8))

    # ---- analytics
    shift_count = 0
    total_hours = 0.0
    for s in shifts:
        hrs = _hours_between(s.shift_date, s.shift_start, s.shift_end)
        total_hours += hrs
        shift_count += 1

    analytics_table = Table(
        [["Metric", "Value"],
         ["Total Shifts", shift_count],
         ["Total Hours", f"{total_hours:.2f}"]],
        hAlign='LEFT'
    )
    analytics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    elems.append(analytics_table)
    elems.append(Spacer(1, 12))

    # ---- shifts table
    data = [["Date", "Staff", "Start", "End", "Hours", "Location"]]
    for s in shifts:
        hrs = _hours_between(s.shift_date, s.shift_start, s.shift_end)
        staff_name = _safe_staff_name(getattr(s, "staff", None), getattr(s, "staff_id", None))
        data.append([
            s.shift_date.isoformat(),
            staff_name,
            _fmt_hhmm(s.shift_start),
            _fmt_hhmm(s.shift_end),
            f"{hrs:.2f}",
            getattr(getattr(s, "location", None), "name", "—"),
        ])

    tbl = Table(data, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (2, 1), (4, -1), "CENTER"),
    ]))

    elems.append(tbl)

    doc.build(elems)
    pdf = buf.getvalue()
    buf.close()
    return pdf


# ------------------------------------------------------------- #
# 2) NEW: Weekly matrix PDF (Staff x 7 days) – like the UI board
# ------------------------------------------------------------- #
def build_weekly_roster_pdf(title, meta_lines, shifts, start_date, end_date):
    """
    Render a 7-day grid: first column 'Staff', next 7 columns each day.
    Multiple shifts per day are shown on separate lines.

    Args:
        title (str)
        meta_lines (list[str])
        shifts (iterable[StaffRoster])
        start_date (date)
        end_date (date)  # inclusive
    """
    buf = BytesIO()

    # a wide table; force landscape
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=0.8 * cm,
        rightMargin=0.8 * cm,
        topMargin=0.8 * cm,
        bottomMargin=0.8 * cm,
    )

    styles = getSampleStyleSheet()
    elems = []

    # header
    elems.append(Paragraph(title, styles["Title"]))
    for ml in meta_lines:
        elems.append(Paragraph(ml, styles["Normal"]))
    elems.append(Spacer(1, 8))

    # build days
    days = []
    d = start_date
    while d <= end_date:
        days.append(d)
        d += timedelta(days=1)

    # group by staff -> date
    # dict[staff_id] = {"name": str, "by_date": dict[date -> [shift, ...]]}
    grouped = {}
    total_hours = 0.0
    total_shifts = 0

    for s in shifts:
        sid = getattr(s, "staff_id", None) or getattr(getattr(s, "staff", None), "id", None)
        if sid is None:
            continue
        staff_name = _safe_staff_name(getattr(s, "staff", None), sid)

        if sid not in grouped:
            grouped[sid] = {"name": staff_name, "by_date": defaultdict(list)}

        grouped[sid]["by_date"][s.shift_date].append(s)

        # counters
        total_hours += _hours_between(s.shift_date, s.shift_start, s.shift_end)
        total_shifts += 1

    # analytics
    analytics_table = Table(
        [
            ["Metric", "Value"],
            ["Total Shifts", total_shifts],
            ["Total Hours", f"{total_hours:.2f}"],
            ["Unique Staff", len(grouped)],
        ],
        hAlign='LEFT'
    )
    analytics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    elems.append(analytics_table)
    elems.append(Spacer(1, 12))

    # build the matrix table
    header = ["Staff"] + [d.strftime("%a %d") for d in days]
    data = [header]

    # sort by name
    sorted_staff = sorted(grouped.values(), key=lambda x: x["name"].lower())

    for g in sorted_staff:
        row = [g["name"]]
        for d in days:
            day_shifts = g["by_date"].get(d, [])
            if not day_shifts:
                row.append("Off")
            else:
                # multiple shifts -> newline
                lines = []
                for s in day_shifts:
                    loc = getattr(getattr(s, "location", None), "name", "") or ""
                    st = _fmt_hhmm(s.shift_start)
                    en = _fmt_hhmm(s.shift_end)
                    lines.append(f"{st}–{en}{(' ' + loc) if loc else ''}")
                row.append("\n".join(lines))
        data.append(row)

    tbl = Table(data, repeatRows=1)

    # Some basic styling
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightyellow]),
        # Make first column (Staff) a bit wider
        ("COLWIDTHS", (0, 0), (0, -1), 4.5 * cm),
    ]))

    elems.append(tbl)

    doc.build(elems)
    pdf = buf.getvalue()
    buf.close()
    return pdf

def build_daily_plan_grouped_pdf(title, meta_lines, entries):
    """
    Generate a PDF showing staff grouped by location.

    Args:
        title (str): PDF title
        meta_lines (list[str]): e.g. date, hotel, department info lines
        entries (list[dict]): each dict has keys like location_name, staff_name, or nested dicts
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=portrait(A4),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
    )
    styles = getSampleStyleSheet()
    elems = []

    # Title + meta
    elems.append(Paragraph(title, styles["Title"]))
    for line in meta_lines:
        elems.append(Paragraph(line, styles["Normal"]))
    elems.append(Spacer(1, 12))

    # Group entries by location
    grouped = defaultdict(list)
    for entry in entries:
        loc = entry.get("location_name") or entry.get("location", {}).get("name") or "No Location"
        staff = entry.get("staff_name") or entry.get("staff", {}).get("full_name") or entry.get("staff", {}).get("name") or "Unknown Staff"
        grouped[loc].append(staff)

    # For each location, print heading and bulleted staff list
    for location, staff_list in grouped.items():
        elems.append(Paragraph(location, styles["Heading2"]))
        staff_items = [ListItem(Paragraph(staff, styles["Normal"]), leftIndent=10) for staff in staff_list]
        elems.append(ListFlowable(staff_items, bulletType="bullet", start="•", leftIndent=15))
        elems.append(Spacer(1, 10))

    doc.build(elems)
    pdf = buf.getvalue()
    buf.close()
    return pdf
