#!/usr/bin/env python
"""
Create comprehensive rosters for Hotel Killarney (ID 2)
- Past rosters (for testing closing logic)
- Current roster (active period)
- Future rosters (for planning)
"""

import os
import sys
import django
from datetime import datetime, date, timedelta, time
import random

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.utils import timezone
from staff.models import Staff, Department, Role
from hotel.models import Hotel
from attendance.models import StaffRoster, RosterPeriod, ClockLog, ShiftLocation
from django.db import transaction


def get_hotel_killarney():
    """Get Hotel Killarney"""
    try:
        hotel = Hotel.objects.get(id=2)
        print(f"✅ Found Hotel: {hotel.name}")
        return hotel
    except Hotel.DoesNotExist:
        print("❌ Hotel Killarney not found!")
        return None


def get_active_staff(hotel):
    """Get all active staff for the hotel"""
    staff = Staff.objects.filter(
        hotel=hotel, 
        is_active=True
    ).select_related('department', 'role').order_by('department__name', 'last_name')
    
    print(f"✅ Found {staff.count()} active staff members")
    return list(staff)


def create_shift_locations(hotel):
    """Create shift locations if they don't exist"""
    locations_data = [
        {'name': 'Reception', 'color': '#0d6efd'},
        {'name': 'Restaurant', 'color': '#dc3545'},
        {'name': 'Bar', 'color': '#fd7e14'},
        {'name': 'Kitchen', 'color': '#198754'},
        {'name': 'Housekeeping', 'color': '#6f42c1'},
        {'name': 'Maintenance', 'color': '#6c757d'},
        {'name': 'Security', 'color': '#495057'},
    ]
    
    locations = []
    for loc_data in locations_data:
        location, created = ShiftLocation.objects.get_or_create(
            hotel=hotel,
            name=loc_data['name'],
            defaults={'color': loc_data['color']}
        )
        locations.append(location)
        if created:
            print(f"   ✅ Created location: {location.name}")
    
    return locations


def create_roster_period(hotel, title, start_date, end_date, is_past=False):
    """Create a roster period"""
    period, created = RosterPeriod.objects.get_or_create(
        hotel=hotel,
        title=title,
        defaults={
            'start_date': start_date,
            'end_date': end_date,
            'published': True,
            'is_finalized': is_past,  # Past periods are finalized
            'created_by': Staff.objects.filter(hotel=hotel, access_level='super_staff_admin').first()
        }
    )
    
    if created:
        status = "PAST (FINALIZED)" if is_past else "ACTIVE/FUTURE"
        print(f"   ✅ Created period: {title} ({status})")
    else:
        print(f"   📋 Period exists: {title}")
    
    return period


def get_shift_patterns():
    """Define common shift patterns"""
    return {
        'morning': {'start': time(7, 0), 'end': time(15, 0), 'break_start': time(11, 0), 'break_end': time(11, 30)},
        'afternoon': {'start': time(15, 0), 'end': time(23, 0), 'break_start': time(19, 0), 'break_end': time(19, 30)},
        'night': {'start': time(23, 0), 'end': time(7, 0), 'break_start': time(3, 0), 'break_end': time(3, 30)},
        'split_morning': {'start': time(7, 0), 'end': time(11, 0), 'break_start': None, 'break_end': None},
        'split_evening': {'start': time(17, 0), 'end': time(23, 0), 'break_start': time(20, 0), 'break_end': time(20, 30)},
        'management': {'start': time(9, 0), 'end': time(17, 0), 'break_start': time(13, 0), 'break_end': time(14, 0)},
        'reception': {'start': time(8, 0), 'end': time(16, 0), 'break_start': time(12, 0), 'break_end': time(12, 30)},
    }


def assign_shift_by_role(role_name, department_name):
    """Assign appropriate shift pattern based on role and department"""
    patterns = get_shift_patterns()
    
    # Department-based assignments
    if department_name in ['Management', 'Marketing']:
        return random.choice(['management'])
    elif department_name == 'Front Office':
        return random.choice(['morning', 'afternoon', 'reception'])
    elif department_name == 'Food and Beverage':
        if 'Manager' in role_name:
            return random.choice(['management', 'afternoon'])
        elif 'Bar' in role_name:
            return random.choice(['afternoon', 'night'])
        else:
            return random.choice(['morning', 'afternoon', 'split_morning'])
    elif department_name == 'Kitchen':
        return random.choice(['morning', 'afternoon', 'split_morning'])
    elif department_name == 'Accommodation':
        return random.choice(['morning', 'afternoon'])
    else:
        return random.choice(['morning', 'afternoon'])


def create_roster_shifts(period, staff_list, locations):
    """Create roster shifts for a period"""
    patterns = get_shift_patterns()
    shifts_created = 0
    
    print(f"   📅 Creating shifts for period: {period.title}")
    
    # Get date range
    current_date = period.start_date
    
    while current_date <= period.end_date:
        # Skip some staff randomly to make it realistic
        working_staff = random.sample(staff_list, k=random.randint(8, 12))
        
        for staff_member in working_staff:
            # Skip weekends for some departments (realistic)
            if current_date.weekday() >= 5:  # Saturday or Sunday
                if staff_member.department and staff_member.department.name in ['Management', 'Marketing']:
                    if random.choice([True, False]):  # 50% chance to skip
                        continue
            
            # Get shift pattern
            dept_name = staff_member.department.name if staff_member.department else 'No Department'
            role_name = staff_member.role.name if staff_member.role else 'No Role'
            pattern_name = assign_shift_by_role(role_name, dept_name)
            pattern = patterns[pattern_name]
            
            # Assign location
            location = None
            if dept_name == 'Front Office':
                location = next((l for l in locations if l.name == 'Reception'), None)
            elif dept_name == 'Food and Beverage':
                if 'Bar' in role_name:
                    location = next((l for l in locations if l.name == 'Bar'), None)
                else:
                    location = next((l for l in locations if l.name == 'Restaurant'), None)
            elif dept_name == 'Kitchen':
                location = next((l for l in locations if l.name == 'Kitchen'), None)
            elif dept_name == 'Accommodation':
                location = next((l for l in locations if l.name == 'Housekeeping'), None)
            elif dept_name == 'Security':
                location = next((l for l in locations if l.name == 'Security'), None)
            
            # Calculate expected hours
            start_dt = datetime.combine(current_date, pattern['start'])
            end_dt = datetime.combine(current_date, pattern['end'])
            
            # Handle night shifts (end next day)
            if pattern['end'] < pattern['start']:
                end_dt += timedelta(days=1)
            
            expected_hours = (end_dt - start_dt).total_seconds() / 3600
            
            # Create the shift
            try:
                shift, created = StaffRoster.objects.get_or_create(
                    hotel=period.hotel,
                    staff=staff_member,
                    period=period,
                    shift_date=current_date,
                    shift_start=pattern['start'],
                    defaults={
                        'shift_end': pattern['end'],
                        'break_start': pattern['break_start'],
                        'break_end': pattern['break_end'],
                        'department': staff_member.department,
                        'shift_type': pattern_name.replace('_', ' '),
                        'is_night_shift': pattern['end'] < pattern['start'],
                        'expected_hours': round(expected_hours, 2),
                        'location': location,
                        'approved_by': Staff.objects.filter(
                            hotel=period.hotel, 
                            access_level='super_staff_admin'
                        ).first(),
                    }
                )
                
                if created:
                    shifts_created += 1
                    
            except Exception as e:
                print(f"   ⚠️ Error creating shift for {staff_member}: {e}")
        
        current_date += timedelta(days=1)
    
    print(f"   ✅ Created {shifts_created} shifts")
    return shifts_created


def create_clock_logs_for_past_shifts(hotel):
    """Create clock logs for past roster shifts to simulate actual attendance"""
    past_periods = RosterPeriod.objects.filter(
        hotel=hotel,
        is_finalized=True,
        end_date__lt=date.today()
    )
    
    logs_created = 0
    
    for period in past_periods:
        print(f"   📅 Creating clock logs for: {period.title}")
        
        past_shifts = StaffRoster.objects.filter(period=period)
        
        for shift in past_shifts:
            # 85% chance staff actually worked the shift
            if random.random() < 0.85:
                # Calculate actual work times with some variation
                planned_start = datetime.combine(shift.shift_date, shift.shift_start)
                planned_end = datetime.combine(shift.shift_date, shift.shift_end)
                
                # Handle night shifts
                if shift.shift_end < shift.shift_start:
                    planned_end += timedelta(days=1)
                
                # Add realistic variation (-15 to +30 minutes start, -30 to +15 minutes end)
                actual_start = planned_start + timedelta(minutes=random.randint(-15, 30))
                actual_end = planned_end + timedelta(minutes=random.randint(-30, 15))
                
                # Make timezone aware
                actual_start = timezone.make_aware(actual_start)
                actual_end = timezone.make_aware(actual_end)
                
                # Create clock log
                try:
                    log, created = ClockLog.objects.get_or_create(
                        hotel=hotel,
                        staff=shift.staff,
                        time_in__date=shift.shift_date,
                        time_in__hour=actual_start.hour,
                        defaults={
                            'time_in': actual_start,
                            'time_out': actual_end,
                            'verified_by_face': random.choice([True, False]),
                            'roster_shift': shift,
                            'is_unrostered': False,
                            'is_approved': True,
                            'location_note': shift.location.name if shift.location else None,
                        }
                    )
                    
                    if created:
                        logs_created += 1
                        
                except Exception as e:
                    print(f"   ⚠️ Error creating log for {shift.staff}: {e}")
    
    print(f"   ✅ Created {logs_created} clock logs")
    return logs_created


def create_comprehensive_rosters(hotel):
    """Create past, current, and future rosters"""
    print(f"\n🎯 CREATING COMPREHENSIVE ROSTERS FOR {hotel.name.upper()}")
    print("=" * 80)
    
    # Get staff and create locations
    staff_list = get_active_staff(hotel)
    locations = create_shift_locations(hotel)
    
    today = date.today()
    monday_this_week = today - timedelta(days=today.weekday())
    
    periods_to_create = []
    
    # Past periods (3 weeks)
    for weeks_ago in range(3, 0, -1):
        start_date = monday_this_week - timedelta(weeks=weeks_ago)
        end_date = start_date + timedelta(days=6)
        title = f'Week {start_date.strftime("%V")} Roster - {start_date.strftime("%B %Y")} (PAST)'
        periods_to_create.append({
            'title': title,
            'start_date': start_date,
            'end_date': end_date,
            'is_past': True
        })
    
    # Current week
    current_start = monday_this_week
    current_end = current_start + timedelta(days=6)
    periods_to_create.append({
        'title': f'Week {current_start.strftime("%V")} Roster - {current_start.strftime("%B %Y")} (CURRENT)',
        'start_date': current_start,
        'end_date': current_end,
        'is_past': False
    })
    
    # Future periods (2 weeks)
    for weeks_ahead in range(1, 3):
        start_date = monday_this_week + timedelta(weeks=weeks_ahead)
        end_date = start_date + timedelta(days=6)
        title = f'Week {start_date.strftime("%V")} Roster - {start_date.strftime("%B %Y")} (FUTURE)'
        periods_to_create.append({
            'title': title,
            'start_date': start_date,
            'end_date': end_date,
            'is_past': False
        })
    
    # Create periods and shifts
    total_shifts = 0
    created_periods = []
    
    with transaction.atomic():
        for period_data in periods_to_create:
            print(f"\n📋 Creating period: {period_data['title']}")
            
            period = create_roster_period(
                hotel=hotel,
                title=period_data['title'],
                start_date=period_data['start_date'],
                end_date=period_data['end_date'],
                is_past=period_data['is_past']
            )
            
            shifts = create_roster_shifts(period, staff_list, locations)
            total_shifts += shifts
            created_periods.append(period)
    
    # Create clock logs for past periods
    print(f"\n⏰ Creating clock logs for past shifts...")
    total_logs = create_clock_logs_for_past_shifts(hotel)
    
    print(f"\n" + "=" * 80)
    print("✅ ROSTER CREATION COMPLETE!")
    print(f"📋 Created {len(created_periods)} periods")
    print(f"📅 Created {total_shifts} roster shifts")
    print(f"⏰ Created {total_logs} clock logs")
    
    return created_periods


def show_roster_summary(hotel):
    """Show summary of all rosters"""
    print(f"\n📊 ROSTER SUMMARY FOR {hotel.name.upper()}")
    print("=" * 60)
    
    periods = RosterPeriod.objects.filter(hotel=hotel).order_by('start_date')
    
    for period in periods:
        shifts_count = StaffRoster.objects.filter(period=period).count()
        logs_count = ClockLog.objects.filter(
            hotel=hotel,
            time_in__date__range=[period.start_date, period.end_date]
        ).count()
        
        status = "FINALIZED" if period.is_finalized else "ACTIVE"
        
        print(f"📅 {period.title}")
        print(f"   📆 {period.start_date} to {period.end_date}")
        print(f"   👥 {shifts_count} shifts scheduled")
        print(f"   ⏰ {logs_count} clock entries")
        print(f"   🔒 Status: {status}")
        print()


def test_closing_logic(hotel):
    """Test roster closing and calculation logic"""
    print(f"\n🧪 TESTING ROSTER CLOSING LOGIC")
    print("=" * 60)
    
    # Get a past finalized period
    past_period = RosterPeriod.objects.filter(
        hotel=hotel,
        is_finalized=True,
        end_date__lt=date.today()
    ).first()
    
    if not past_period:
        print("❌ No past finalized period found for testing")
        return
    
    print(f"🔍 Testing period: {past_period.title}")
    
    # Get all shifts for this period
    shifts = StaffRoster.objects.filter(period=past_period).select_related('staff')
    
    total_planned_hours = 0
    total_actual_hours = 0
    attendance_rate = 0
    
    for shift in shifts:
        # Calculate planned hours
        if shift.expected_hours:
            total_planned_hours += float(shift.expected_hours)
        
        # Get actual clock logs for this shift
        logs = ClockLog.objects.filter(
            hotel=hotel,
            staff=shift.staff,
            time_in__date=shift.shift_date,
            is_approved=True
        )
        
        for log in logs:
            if log.hours_worked:
                total_actual_hours += float(log.hours_worked)
    
    shifts_with_attendance = ClockLog.objects.filter(
        hotel=hotel,
        time_in__date__range=[past_period.start_date, past_period.end_date],
        is_approved=True
    ).count()
    
    total_shifts = shifts.count()
    attendance_rate = (shifts_with_attendance / total_shifts * 100) if total_shifts > 0 else 0
    
    print(f"📊 Period Analysis:")
    print(f"   📅 Total Shifts: {total_shifts}")
    print(f"   ⏰ Planned Hours: {total_planned_hours:.2f}")
    print(f"   ✅ Actual Hours: {total_actual_hours:.2f}")
    print(f"   📈 Attendance Rate: {attendance_rate:.1f}%")
    print(f"   🎯 Hours Variance: {total_actual_hours - total_planned_hours:+.2f}")
    
    if attendance_rate > 80:
        print("   ✅ Good attendance rate!")
    elif attendance_rate > 60:
        print("   ⚠️ Moderate attendance rate")
    else:
        print("   ❌ Low attendance rate")


def main():
    """Main function"""
    print("🏨 KILLARNEY HOTEL ROSTER CREATION SYSTEM")
    print("=" * 80)
    
    # Get hotel
    hotel = get_hotel_killarney()
    if not hotel:
        return
    
    # Create comprehensive rosters
    created_periods = create_comprehensive_rosters(hotel)
    
    # Show summary
    show_roster_summary(hotel)
    
    # Test closing logic
    test_closing_logic(hotel)
    
    print(f"\n🎉 ALL ROSTERS CREATED SUCCESSFULLY!")
    print("You can now test:")
    print("   • Past roster closing logic")
    print("   • Current roster management") 
    print("   • Future roster planning")
    print("   • Attendance tracking")
    print("   • Hours calculation")


if __name__ == "__main__":
    main()