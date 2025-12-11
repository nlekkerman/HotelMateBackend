#!/usr/bin/env python
"""
Clock Logs Analyzer - Fetch All Clock Logs & Check Working Time
===============================================================

This script fetches all clock logs and analyzes working time patterns:
1. Gets all clock logs for specified period
2. Calculates working hours per staff member
3. Identifies attendance issues (long sessions, missing clock-outs)
4. Shows department summaries
5. Exports data for analysis

Usage:
    python analyze_clock_logs.py --days 30          # Last 30 days
    python analyze_clock_logs.py --hotel killarney  # Specific hotel
    python analyze_clock_logs.py --staff-id 123     # Specific staff
    python analyze_clock_logs.py --export csv       # Export to CSV
"""
import os
import sys
import django
from datetime import datetime, timedelta, time
from decimal import Decimal
import csv

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import transaction
from django.utils.timezone import now, make_aware
from django.db.models import Sum, Count, Avg, Q, Max, Min
from hotel.models import Hotel
from attendance.models import ClockLog
from staff.models import Staff
import argparse


def print_separator(title):
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)


def format_duration(hours):
    """Convert decimal hours to readable format"""
    if not hours:
        return "0h 0m"
    
    total_hours = int(hours)
    minutes = int((hours - total_hours) * 60)
    return f"{total_hours}h {minutes}m"


def get_clock_logs(hotel=None, staff_id=None, days=7, date_from=None, date_to=None):
    """Fetch clock logs with filters"""
    
    # Calculate date range
    if date_from and date_to:
        start_date = date_from
        end_date = date_to
    else:
        end_date = now().date()
        start_date = end_date - timedelta(days=days)
    
    # Base queryset
    queryset = ClockLog.objects.select_related(
        'staff', 'hotel', 'staff__department', 'roster_shift'
    ).filter(
        time_in__date__range=[start_date, end_date]
    ).order_by('-time_in')
    
    # Apply filters
    if hotel:
        queryset = queryset.filter(hotel=hotel)
    
    if staff_id:
        queryset = queryset.filter(staff_id=staff_id)
    
    print(f"📅 Analyzing period: {start_date} to {end_date}")
    print(f"🔍 Total clock logs found: {queryset.count()}")
    
    return queryset, start_date, end_date


def analyze_working_time(logs):
    """Analyze working time patterns"""
    
    print_separator("WORKING TIME ANALYSIS")
    
    # Overall stats
    total_logs = logs.count()
    completed_logs = logs.filter(time_out__isnull=False).count()
    open_logs = logs.filter(time_out__isnull=True).count()
    
    print(f"📊 Log Status Overview:")
    print(f"  Total logs: {total_logs}")
    print(f"  Completed shifts: {completed_logs}")
    print(f"  Currently clocked in: {open_logs}")
    
    # Hours worked statistics
    completed_logs_qs = logs.filter(
        time_out__isnull=False, 
        hours_worked__isnull=False,
        is_approved=True
    )
    
    if completed_logs_qs.exists():
        stats = completed_logs_qs.aggregate(
            total_hours=Sum('hours_worked'),
            avg_hours=Avg('hours_worked'),
            max_hours=Max('hours_worked'),
            min_hours=Min('hours_worked')
        )
        
        print(f"\n⏰ Working Hours Statistics:")
        print(f"  Total hours worked: {format_duration(stats['total_hours'] or 0)}")
        print(f"  Average shift length: {format_duration(stats['avg_hours'] or 0)}")
        print(f"  Longest shift: {format_duration(stats['max_hours'] or 0)}")
        print(f"  Shortest shift: {format_duration(stats['min_hours'] or 0)}")


def analyze_by_staff(logs):
    """Analyze working time by staff member"""
    
    print_separator("STAFF WORKING TIME BREAKDOWN")
    
    # Group by staff
    staff_stats = {}
    
    for log in logs:
        staff_name = f"{log.staff.first_name} {log.staff.last_name}"
        dept_name = log.staff.department.name if log.staff.department else "No Department"
        
        if staff_name not in staff_stats:
            staff_stats[staff_name] = {
                'department': dept_name,
                'total_hours': Decimal('0'),
                'shift_count': 0,
                'open_sessions': 0,
                'issues': [],
                'staff_id': log.staff.id
            }
        
        staff_data = staff_stats[staff_name]
        
        # Count shifts
        staff_data['shift_count'] += 1
        
        # Add hours if completed
        if log.time_out and log.hours_worked and log.is_approved:
            staff_data['total_hours'] += log.hours_worked
        
        # Check for open sessions
        if not log.time_out:
            staff_data['open_sessions'] += 1
            duration = now() - log.time_in
            hours = duration.total_seconds() / 3600
            staff_data['issues'].append(f"Open session: {format_duration(hours)}")
        
        # Check for long shifts (>12 hours)
        if log.hours_worked and log.hours_worked > 12:
            staff_data['issues'].append(f"Long shift: {format_duration(log.hours_worked)}")
        
        # Check for unrostered work
        if log.is_unrostered and not log.is_approved:
            staff_data['issues'].append("Unrostered shift pending approval")
        
        # Check for rejected logs
        if log.is_rejected:
            staff_data['issues'].append("Rejected shift")
    
    # Sort by total hours (descending)
    sorted_staff = sorted(staff_stats.items(), key=lambda x: x[1]['total_hours'], reverse=True)
    
    print(f"👥 Staff Members ({len(sorted_staff)} total):")
    print()
    
    for staff_name, data in sorted_staff:
        issues_text = " | ".join(data['issues']) if data['issues'] else "No issues"
        avg_hours = data['total_hours'] / data['shift_count'] if data['shift_count'] > 0 else 0
        
        print(f"  👤 {staff_name} (ID: {data['staff_id']})")
        print(f"      Department: {data['department']}")
        print(f"      Total hours: {format_duration(data['total_hours'])}")
        print(f"      Shifts: {data['shift_count']}")
        print(f"      Average shift: {format_duration(avg_hours)}")
        print(f"      Open sessions: {data['open_sessions']}")
        print(f"      Issues: {issues_text}")
        print()


def analyze_by_department(logs):
    """Analyze working time by department"""
    
    print_separator("DEPARTMENT WORKING TIME BREAKDOWN")
    
    # Group by department
    dept_stats = {}
    
    for log in logs:
        dept_name = log.staff.department.name if log.staff.department else "No Department"
        
        if dept_name not in dept_stats:
            dept_stats[dept_name] = {
                'total_hours': Decimal('0'),
                'shift_count': 0,
                'staff_count': set(),
                'open_sessions': 0,
                'issues': 0
            }
        
        dept_data = dept_stats[dept_name]
        
        # Count shifts and staff
        dept_data['shift_count'] += 1
        dept_data['staff_count'].add(log.staff.id)
        
        # Add hours if completed
        if log.time_out and log.hours_worked and log.is_approved:
            dept_data['total_hours'] += log.hours_worked
        
        # Count open sessions
        if not log.time_out:
            dept_data['open_sessions'] += 1
        
        # Count issues
        if (log.is_unrostered and not log.is_approved) or log.is_rejected:
            dept_data['issues'] += 1
        
        if log.hours_worked and log.hours_worked > 12:
            dept_data['issues'] += 1
    
    # Sort by total hours
    sorted_depts = sorted(dept_stats.items(), key=lambda x: x[1]['total_hours'], reverse=True)
    
    print(f"🏢 Departments ({len(sorted_depts)} total):")
    print()
    
    for dept_name, data in sorted_depts:
        staff_count = len(data['staff_count'])
        avg_hours_per_staff = data['total_hours'] / staff_count if staff_count > 0 else 0
        
        print(f"  🏢 {dept_name}")
        print(f"      Total hours: {format_duration(data['total_hours'])}")
        print(f"      Staff members: {staff_count}")
        print(f"      Total shifts: {data['shift_count']}")
        print(f"      Avg hours per staff: {format_duration(avg_hours_per_staff)}")
        print(f"      Open sessions: {data['open_sessions']}")
        print(f"      Issues: {data['issues']}")
        print()


def check_attendance_issues(logs):
    """Check for various attendance issues"""
    
    print_separator("ATTENDANCE ISSUES ANALYSIS")
    
    issues = {
        'open_sessions': [],
        'long_shifts': [],
        'unrostered_pending': [],
        'rejected_logs': [],
        'missing_clockouts': [],
        'excessive_hours': []
    }
    
    current_time = now()
    
    for log in logs:
        staff_name = f"{log.staff.first_name} {log.staff.last_name}"
        
        # Open sessions (no clock-out)
        if not log.time_out:
            duration = current_time - log.time_in
            hours = duration.total_seconds() / 3600
            issues['open_sessions'].append({
                'staff': staff_name,
                'duration': hours,
                'clock_in': log.time_in,
                'log_id': log.id
            })
            
            # Missing clock-out (older than 24 hours)
            if hours > 24:
                issues['missing_clockouts'].append({
                    'staff': staff_name,
                    'duration': hours,
                    'clock_in': log.time_in,
                    'log_id': log.id
                })
        
        # Long shifts (>12 hours)
        if log.hours_worked and log.hours_worked > 12:
            issues['long_shifts'].append({
                'staff': staff_name,
                'hours': log.hours_worked,
                'date': log.time_in.date(),
                'log_id': log.id
            })
        
        # Excessive hours (>16 hours)
        if log.hours_worked and log.hours_worked > 16:
            issues['excessive_hours'].append({
                'staff': staff_name,
                'hours': log.hours_worked,
                'date': log.time_in.date(),
                'log_id': log.id
            })
        
        # Unrostered pending approval
        if log.is_unrostered and not log.is_approved and not log.is_rejected:
            issues['unrostered_pending'].append({
                'staff': staff_name,
                'date': log.time_in.date(),
                'log_id': log.id
            })
        
        # Rejected logs
        if log.is_rejected:
            issues['rejected_logs'].append({
                'staff': staff_name,
                'date': log.time_in.date(),
                'log_id': log.id
            })
    
    # Report issues
    print("🚨 Attendance Issues Found:")
    print()
    
    if issues['open_sessions']:
        print(f"  ⏰ Open Sessions ({len(issues['open_sessions'])}):")
        for issue in issues['open_sessions'][:10]:  # Show first 10
            print(f"    - {issue['staff']}: {format_duration(issue['duration'])} (ID: {issue['log_id']})")
        if len(issues['open_sessions']) > 10:
            print(f"    ... and {len(issues['open_sessions']) - 10} more")
        print()
    
    if issues['missing_clockouts']:
        print(f"  ❌ Missing Clock-outs (>24h) ({len(issues['missing_clockouts'])}):")
        for issue in issues['missing_clockouts']:
            print(f"    - {issue['staff']}: {format_duration(issue['duration'])} (ID: {issue['log_id']})")
        print()
    
    if issues['long_shifts']:
        print(f"  ⚠️ Long Shifts (>12h) ({len(issues['long_shifts'])}):")
        for issue in issues['long_shifts'][:5]:  # Show first 5
            print(f"    - {issue['staff']}: {format_duration(issue['hours'])} on {issue['date']} (ID: {issue['log_id']})")
        if len(issues['long_shifts']) > 5:
            print(f"    ... and {len(issues['long_shifts']) - 5} more")
        print()
    
    if issues['excessive_hours']:
        print(f"  🔥 Excessive Hours (>16h) ({len(issues['excessive_hours'])}):")
        for issue in issues['excessive_hours']:
            print(f"    - {issue['staff']}: {format_duration(issue['hours'])} on {issue['date']} (ID: {issue['log_id']})")
        print()
    
    if issues['unrostered_pending']:
        print(f"  ⏳ Unrostered Pending Approval ({len(issues['unrostered_pending'])}):")
        for issue in issues['unrostered_pending'][:5]:
            print(f"    - {issue['staff']} on {issue['date']} (ID: {issue['log_id']})")
        if len(issues['unrostered_pending']) > 5:
            print(f"    ... and {len(issues['unrostered_pending']) - 5} more")
        print()
    
    if issues['rejected_logs']:
        print(f"  ❌ Rejected Logs ({len(issues['rejected_logs'])}):")
        for issue in issues['rejected_logs']:
            print(f"    - {issue['staff']} on {issue['date']} (ID: {issue['log_id']})")
        print()
    
    if not any(issues.values()):
        print("  ✅ No attendance issues found!")


def export_to_csv(logs, filename=None):
    """Export clock logs to CSV"""
    
    if not filename:
        filename = f"clock_logs_{now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    print_separator(f"EXPORTING TO CSV: {filename}")
    
    fieldnames = [
        'log_id', 'hotel', 'staff_name', 'staff_id', 'department',
        'time_in', 'time_out', 'hours_worked', 'date', 'day_of_week',
        'verified_by_face', 'auto_clock_out', 'is_unrostered', 
        'is_approved', 'is_rejected', 'roster_shift_id', 'location_note'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for log in logs:
            writer.writerow({
                'log_id': log.id,
                'hotel': log.hotel.name,
                'staff_name': f"{log.staff.first_name} {log.staff.last_name}",
                'staff_id': log.staff.id,
                'department': log.staff.department.name if log.staff.department else '',
                'time_in': log.time_in.isoformat(),
                'time_out': log.time_out.isoformat() if log.time_out else '',
                'hours_worked': str(log.hours_worked) if log.hours_worked else '',
                'date': log.time_in.date(),
                'day_of_week': log.time_in.strftime('%A'),
                'verified_by_face': log.verified_by_face,
                'auto_clock_out': log.auto_clock_out,
                'is_unrostered': log.is_unrostered,
                'is_approved': log.is_approved,
                'is_rejected': log.is_rejected,
                'roster_shift_id': log.roster_shift_id if log.roster_shift else '',
                'location_note': log.location_note or ''
            })
    
    print(f"✅ Exported {logs.count()} logs to {filename}")


def main():
    """Main execution function"""
    
    parser = argparse.ArgumentParser(description='Analyze clock logs and working time')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze (default: 7)')
    parser.add_argument('--hotel', help='Hotel slug to filter by')
    parser.add_argument('--staff-id', type=int, help='Staff ID to filter by')
    parser.add_argument('--date-from', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--date-to', help='End date (YYYY-MM-DD)')
    parser.add_argument('--export', choices=['csv'], help='Export format')
    parser.add_argument('--filename', help='Export filename')
    
    args = parser.parse_args()
    
    print_separator("CLOCK LOGS ANALYZER")
    
    # Parse dates
    date_from = None
    date_to = None
    if args.date_from:
        date_from = datetime.strptime(args.date_from, '%Y-%m-%d').date()
    if args.date_to:
        date_to = datetime.strptime(args.date_to, '%Y-%m-%d').date()
    
    # Get hotel if specified
    hotel = None
    if args.hotel:
        try:
            hotel = Hotel.objects.get(slug=args.hotel)
            print(f"🏨 Filtering by hotel: {hotel.name}")
        except Hotel.DoesNotExist:
            print(f"❌ Hotel '{args.hotel}' not found!")
            return
    
    # Get clock logs
    try:
        logs, start_date, end_date = get_clock_logs(
            hotel=hotel,
            staff_id=args.staff_id,
            days=args.days,
            date_from=date_from,
            date_to=date_to
        )
        
        if not logs.exists():
            print("❌ No clock logs found for the specified criteria!")
            return
        
        # Run analysis
        analyze_working_time(logs)
        analyze_by_staff(logs)
        analyze_by_department(logs)
        check_attendance_issues(logs)
        
        # Export if requested
        if args.export == 'csv':
            export_to_csv(logs, args.filename)
        
        print_separator("ANALYSIS COMPLETE")
        
    except Exception as e:
        print(f"❌ Error analyzing clock logs: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()