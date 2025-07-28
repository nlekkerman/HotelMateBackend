import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()

from staff.models import Department, Role

roles_data = {
    "front-office": {
        "receptionist": "Manages guest check-ins, check-outs, and reservation details.",
        "concierge": "Provides guests with information, booking services, and assistance.",
        "guest_relations_officer": "Handles guest complaints and feedback ensuring satisfaction.",
        "front_office_manager": "Supervises front office staff and coordinates daily operations.",
        "reservation_agent": "Manages room bookings and availability.",
        "porter": "Assists guests with luggage and escorts to rooms."
    },
    "kitchen": {
        "head_chef": "Leads the kitchen team, plans menus, and ensures culinary excellence.",
        "sous_chef": "Second in command, assists head chef and oversees kitchen operations.",
        "line_cook": "Prepares dishes according to recipes and standards.",
        "prep_cook": "Prepares ingredients and supports kitchen staff.",
        "pastry_chef": "Specializes in desserts and baked goods.",
        "kitchen_helper": "Maintains cleanliness and assists cooks as needed."
    },
    "food-and-beverage": {
        "food_and_beverage_manager": "Oversees restaurant and bar operations ensuring excellent service.",
        "bar_manager": "Responsible for managing bar operations and staff.",
        "head_waiter": "Leads waitstaff and ensures quality table service.",
        "waiter": "Provides table service to guests with professionalism.",
        "bar_staff": "Prepares and serves drinks to guests.",
        "room_service_waiter": "Delivers food and beverages to guest rooms.",
        "banquet_manager": "Manages banquet and event food service operations.",
        "food_runner": "Assists with delivering food from kitchen to tables efficiently.",
        "commis_waiter": "Supports waitstaff with basic service tasks."
    },
    "accommodation": {
        "housekeeping_manager": "Leads housekeeping staff and maintains room standards.",
        "housekeeper": "Cleans and prepares guest rooms and public areas.",
        "laundry_attendant": "Manages laundry services and linen care.",
        "room_attendant": "Prepares and stocks guest rooms with amenities.",
        "floor_supervisor": "Coordinates housekeeping activities on assigned floors."
    },
    "accountants_and_payroll": {
        "payroll_officer": "Handles salaries, timesheets, deductions, and benefits.",
        "accountant": "Manages financial records, budgets, and reporting.",
        "accounts_payable_clerk": "Processes supplier invoices and payments.",
        "accounts_receivable_clerk": "Manages incoming payments and billing.",
        "finance_manager": "Oversees financial operations and compliance."
    },
    "human_resources": {
        "hr_manager": "Leads recruitment, employee relations, and policy enforcement.",
        "recruiter": "Sources and hires qualified candidates.",
        "training_coordinator": "Plans and implements staff training programs.",
        "hr_officer": "Handles day-to-day HR administration and employee welfare.",
        "compliance_officer": "Ensures adherence to labor laws and company policies."
    },
    "management": {
        "general_manager": "Provides overall leadership and strategic direction.",
        "duty_manager": "Oversees hotel operations and interdepartmental coordination.",
        "finance_director": "Leads financial planning and control.",
        "marketing_manager": "Manages hotel branding, advertising, and promotions.",
        "sales_manager": "Leads sales initiatives and client relationships.",
        "deputy_manager": "Supports general manager in daily operations."
    },
    "leisure": {
        "spa_manager": "Oversees spa operations and guest services.",
        "fitness_instructor": "Conducts fitness classes and personal training.",
        "lifeguard": "Ensures safety in pools and recreational water areas.",
        "recreation_coordinator": "Plans leisure activities and entertainment.",
        "wellness_coach": "Guides guests on wellness programs."
    },
    "maintenance": {
        "maintenance_manager": "Leads maintenance team and schedules repairs.",
        "electrician": "Handles electrical systems and troubleshooting.",
        "plumber": "Manages plumbing installations and repairs.",
        "hvac_technician": "Maintains heating, ventilation, and air conditioning systems.",
        "general_maintenance_worker": "Performs routine maintenance and repairs."
    },
    "security": {
        "security_manager": "Oversees hotel security operations and protocols.",
        "security_officer": "Patrols premises and monitors surveillance.",
        "loss_prevention_officer": "Prevents theft and manages incident reports.",
        "access_control_officer": "Manages entry and exit points for safety.",
        "emergency_response_coordinator": "Coordinates emergency preparedness and response."
    },
    "delivery": {
        "delivery_coordinator": "Schedules and manages delivery logistics within the hotel.",
        "courier": "Transports food, supplies, and items promptly and safely.",
        "inventory_runner": "Delivers inventory and supports stock replenishment.",
        "logistics_assistant": "Assists with organizing and tracking deliveries.",
        "delivery_driver": "Operates vehicles to transport goods externally and internally."
    }
}

def create_roles():
    for dept_slug, roles in roles_data.items():
        try:
            department = Department.objects.get(slug=dept_slug)
        except Department.DoesNotExist:
            print(f"Department '{dept_slug}' not found. Skipping...")
            continue
        
        for role_slug, role_desc in roles.items():
            role_name = role_slug.replace('_', ' ').title()
            role, created = Role.objects.get_or_create(
                slug=role_slug,
                defaults={
                    "name": role_name,
                    "description": role_desc,
                    "department": department
                }
            )
            if created:
                print(f"Created role '{role_name}' in department '{department.name}'")
            else:
                # Optionally update department if it’s missing
                if role.department != department:
                    role.department = department
                    role.save()
                print(f"Role '{role_name}' already exists in department '{department.name}'")

if __name__ == "__main__":
    create_roles()
    print("Role creation process completed.")
