#!/usr/bin/env python
"""
Fetch all staff and departments for Hotel Killarney (ID 2)
Check all names from models and serializers for creating rosters in the past.
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.db import models
from staff.models import Staff, Department, Role
from hotel.models import Hotel
from attendance.models import StaffRoster, RosterPeriod, ClockLog
from django.utils import timezone
from datetime import datetime, date, timedelta


def fetch_hotel_killarney():
    """Fetch Hotel Killarney by ID 2 or name"""
    try:
        # Try by ID first
        hotel = Hotel.objects.get(id=2)
        print(f"✅ Found Hotel by ID 2: {hotel.name} (slug: {hotel.slug})")
        return hotel
    except Hotel.DoesNotExist:
        try:
            # Try by name/slug containing killarney
            hotel = Hotel.objects.filter(
                models.Q(name__icontains='killarney') | 
                models.Q(slug__icontains='killarney')
            ).first()
            if hotel:
                print(f"✅ Found Hotel by name/slug: {hotel.name} (ID: {hotel.id}, slug: {hotel.slug})")
                return hotel
            else:
                print("❌ No hotel found with 'killarney' in name or slug")
                return None
        except Exception as e:
            print(f"❌ Error searching for hotel: {e}")
            return None


def fetch_all_departments():
    """Fetch all departments in the system"""
    departments = Department.objects.all().order_by('name')
    print(f"\n📋 SYSTEM DEPARTMENTS ({departments.count()})")
    print("=" * 60)
    
    for dept in departments:
        roles_count = Role.objects.filter(department=dept).count()
        staff_count = Staff.objects.filter(department=dept).count()
        
        print(f"🏢 {dept.name} (slug: {dept.slug})")
        print(f"   📝 Description: {dept.description or 'No description'}")
        print(f"   👥 Staff Count: {staff_count}")
        print(f"   🎭 Roles Count: {roles_count}")
        
        # List roles for this department
        roles = Role.objects.filter(department=dept).order_by('name')
        for role in roles:
            role_staff_count = Staff.objects.filter(role=role).count()
            print(f"      → {role.name} (slug: {role.slug}) - {role_staff_count} staff")
        
        print()
    
    return departments


def fetch_hotel_staff(hotel):
    """Fetch all staff for the given hotel"""
    if not hotel:
        return []
    
    staff = Staff.objects.filter(hotel=hotel).select_related('department', 'role', 'user').order_by('department__name', 'last_name', 'first_name')
    
    print(f"\n👥 HOTEL STAFF FOR {hotel.name.upper()} ({staff.count()})")
    print("=" * 60)
    
    current_dept = None
    for staff_member in staff:
        # Group by department
        if current_dept != staff_member.department:
            current_dept = staff_member.department
            dept_name = current_dept.name if current_dept else "No Department"
            print(f"\n🏢 {dept_name}")
            print("-" * 40)
        
        # Staff details
        full_name = f"{staff_member.first_name} {staff_member.last_name}".strip()
        role_name = staff_member.role.name if staff_member.role else "No Role"
        
        print(f"   👤 {full_name}")
        print(f"      📧 Email: {staff_member.email or 'No email'}")
        print(f"      📞 Phone: {staff_member.phone_number or 'No phone'}")
        print(f"      🎭 Role: {role_name}")
        print(f"      🆔 Staff ID: {staff_member.id}")
        print(f"      ✅ Active: {'Yes' if staff_member.is_active else 'No'}")
        print(f"      🔒 Access Level: {staff_member.get_access_level_display()}")
        print(f"      📊 Duty Status: {staff_member.get_duty_status_display()}")
        
        # Check if has face registration
        face_registered = hasattr(staff_member, 'face_data') and staff_member.face_data
        print(f"      👁️ Face Registered: {'Yes' if face_registered else 'No'}")
        
        # Check if has user account
        user_account = "Yes" if staff_member.user else "No"
        print(f"      🔑 User Account: {user_account}")
        
        print()
    
    return staff


def check_existing_rosters(hotel):
    """Check existing rosters for the hotel"""
    if not hotel:
        return
    
    print(f"\n📅 EXISTING ROSTERS FOR {hotel.name.upper()}")
    print("=" * 60)
    
    # Check roster periods
    periods = RosterPeriod.objects.filter(hotel=hotel).order_by('-start_date')
    print(f"📋 Roster Periods: {periods.count()}")
    
    for period in periods[:5]:  # Show last 5 periods
        entries_count = StaffRoster.objects.filter(period=period).count()
        print(f"   📆 {period.title}")
        print(f"      📅 Date Range: {period.start_date} to {period.end_date}")
        print(f"      👥 Entries: {entries_count}")
        print(f"      ✅ Published: {'Yes' if period.published else 'No'}")
        print(f"      🔒 Finalized: {'Yes' if period.is_finalized else 'No'}")
        print()
    
    # Check recent roster entries
    recent_rosters = StaffRoster.objects.filter(hotel=hotel).select_related('staff', 'department', 'period').order_by('-shift_date')[:10]
    print(f"📝 Recent Roster Entries (Last 10):")
    
    for roster in recent_rosters:
        staff_name = f"{roster.staff.first_name} {roster.staff.last_name}".strip()
        dept_name = roster.department.name if roster.department else "No Dept"
        
        print(f"   📅 {roster.shift_date} | {roster.shift_start}-{roster.shift_end}")
        print(f"      👤 {staff_name} ({dept_name})")
        print(f"      🕐 Type: {roster.get_shift_type_display()}")
        print(f"      ⏰ Expected Hours: {roster.expected_hours or 'Not set'}")
        print()


def check_clock_logs(hotel):
    """Check recent clock logs"""
    if not hotel:
        return
    
    print(f"\n⏰ RECENT CLOCK LOGS FOR {hotel.name.upper()}")
    print("=" * 60)
    
    recent_logs = ClockLog.objects.filter(hotel=hotel).select_related('staff').order_by('-time_in')[:10]
    
    for log in recent_logs:
        staff_name = f"{log.staff.first_name} {log.staff.last_name}".strip()
        time_out_str = log.time_out.strftime('%H:%M') if log.time_out else "Still clocked in"
        
        print(f"   📅 {log.time_in.strftime('%Y-%m-%d %H:%M')}")
        print(f"      👤 {staff_name}")
        print(f"      ⏰ Out: {time_out_str}")
        print(f"      🕐 Hours: {log.hours_worked or 'Calculating...'}")
        print(f"      👁️ Face Verified: {'Yes' if log.verified_by_face else 'No'}")
        print(f"      ✅ Approved: {'Yes' if log.is_approved else 'No'}")
        print()


def check_models_and_serializers():
    """Check all model and serializer names"""
    print(f"\n🔍 MODELS AND SERIALIZERS ANALYSIS")
    print("=" * 60)
    
    # Staff related models
    print("📋 STAFF MODELS:")
    print(f"   • Staff model fields: {[f.name for f in Staff._meta.fields]}")
    print(f"   • Department model fields: {[f.name for f in Department._meta.fields]}")
    print(f"   • Role model fields: {[f.name for f in Role._meta.fields]}")
    
    # Attendance models
    print("\n📋 ATTENDANCE MODELS:")
    print(f"   • StaffRoster fields: {[f.name for f in StaffRoster._meta.fields]}")
    print(f"   • RosterPeriod fields: {[f.name for f in RosterPeriod._meta.fields]}")
    print(f"   • ClockLog fields: {[f.name for f in ClockLog._meta.fields]}")
    
    # Import serializers to check
    try:
        from staff.serializers import StaffSerializer, DepartmentSerializer, RoleSerializer
        from attendance.serializers import StaffRosterSerializer
        
        print("\n📋 AVAILABLE SERIALIZERS:")
        print("   • StaffSerializer ✅")
        print("   • DepartmentSerializer ✅")
        print("   • RoleSerializer ✅") 
        print("   • StaffRosterSerializer ✅")
        
        # Show serializer field names
        staff_serializer = StaffSerializer()
        print(f"\n   StaffSerializer fields: {list(staff_serializer.fields.keys())}")
        
        dept_serializer = DepartmentSerializer()
        print(f"   DepartmentSerializer fields: {list(dept_serializer.fields.keys())}")
        
        roster_serializer = StaffRosterSerializer()
        print(f"   StaffRosterSerializer fields: {list(roster_serializer.fields.keys())}")
        
    except ImportError as e:
        print(f"   ❌ Error importing serializers: {e}")


def analyze_staff_names(staff):
    """Analyze staff names for potential issues"""
    print(f"\n📊 STAFF NAME ANALYSIS")
    print("=" * 60)
    
    issues = []
    
    for staff_member in staff:
        name_issues = []
        
        # Check for empty names
        if not staff_member.first_name.strip():
            name_issues.append("Empty first name")
        
        if not staff_member.last_name.strip():
            name_issues.append("Empty last name")
        
        # Check for special characters
        import re
        if not re.match(r'^[a-zA-Z\s\'-]+$', staff_member.first_name):
            name_issues.append("Special characters in first name")
        
        if not re.match(r'^[a-zA-Z\s\'-]+$', staff_member.last_name):
            name_issues.append("Special characters in last name")
        
        if name_issues:
            full_name = f"{staff_member.first_name} {staff_member.last_name}".strip()
            issues.append({
                'id': staff_member.id,
                'name': full_name,
                'issues': name_issues
            })
    
    if issues:
        print("⚠️ FOUND NAME ISSUES:")
        for issue in issues:
            print(f"   👤 {issue['name']} (ID: {issue['id']})")
            for problem in issue['issues']:
                print(f"      ⚠️ {problem}")
            print()
    else:
        print("✅ All staff names look good!")


def create_test_roster_data(hotel, staff):
    """Suggest test roster data for past periods"""
    if not hotel or not staff:
        return
    
    print(f"\n🎯 SUGGESTED TEST ROSTER CREATION")
    print("=" * 60)
    
    print("📅 We can create roster periods for:")
    
    # Suggest periods in the past
    today = date.today()
    suggested_periods = []
    
    for weeks_ago in range(1, 5):  # 1-4 weeks ago
        start_date = today - timedelta(weeks=weeks_ago, days=today.weekday())
        end_date = start_date + timedelta(days=6)
        
        suggested_periods.append({
            'title': f'Week {start_date.strftime("%V")} Roster - {start_date.strftime("%B %Y")}',
            'start_date': start_date,
            'end_date': end_date,
            'weeks_ago': weeks_ago
        })
    
    for period in suggested_periods:
        print(f"   📋 {period['title']}")
        print(f"      📅 {period['start_date']} to {period['end_date']} ({period['weeks_ago']} weeks ago)")
        print()
    
    print("👥 Available staff for rosters:")
    active_staff = [s for s in staff if s.is_active]
    
    by_department = {}
    for staff_member in active_staff:
        dept_name = staff_member.department.name if staff_member.department else "No Department"
        if dept_name not in by_department:
            by_department[dept_name] = []
        by_department[dept_name].append(staff_member)
    
    for dept, members in by_department.items():
        print(f"   🏢 {dept} ({len(members)} staff)")
        for member in members:
            full_name = f"{member.first_name} {member.last_name}".strip()
            role = member.role.name if member.role else "No Role"
            print(f"      👤 {full_name} ({role})")
        print()
    
    print("🚀 Next steps:")
    print("   1. Choose a past period to create rosters for")
    print("   2. Create StaffRoster entries for different staff members")
    print("   3. Create ClockLog entries to simulate actual attendance")
    print("   4. Test roster closing logic and calculations")


def main():
    """Main function to run all checks"""
    print("🏨 KILLARNEY HOTEL STAFF & DEPARTMENT ANALYSIS")
    print("=" * 80)
    
    # 1. Fetch hotel
    hotel = fetch_hotel_killarney()
    
    # 2. Fetch all departments
    departments = fetch_all_departments()
    
    # 3. Fetch hotel staff
    staff = fetch_hotel_staff(hotel) if hotel else []
    
    # 4. Check existing rosters
    if hotel:
        check_existing_rosters(hotel)
        check_clock_logs(hotel)
    
    # 5. Check models and serializers
    check_models_and_serializers()
    
    # 6. Analyze staff names
    if staff:
        analyze_staff_names(staff)
    
    # 7. Suggest test data creation
    if hotel and staff:
        create_test_roster_data(hotel, staff)
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print(f"📊 Found {len(departments)} departments and {len(staff)} staff members for {hotel.name if hotel else 'hotel not found'}")


if __name__ == "__main__":
    main()