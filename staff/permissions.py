from staff.models import Staff

# Define all your roles by department and their slugs exactly as you gave:

NAV_ACCESS_RULES = {
    "accommodation_panel": {
        "access_levels": ["regular_staff", "staff_admin", "super_staff_admin"],
        "departments": ["accommodation"],
        "roles": [
            "floor_supervisor",
            "housekeeper",
            "housekeeping_manager",
            "laundry_attendant",
            "room_attendant",
        ],
    },
    "delivery_panel": {
        "access_levels": ["regular_staff", "staff_admin", "super_staff_admin"],
        "departments": ["delivery"],
        "roles": [
            "courier",
            "delivery_coordinator",
            "delivery_driver",
            "inventory_runner",
            "logistics_assistant",
        ],
    },
    "food_and_beverage_panel": {
        "access_levels": ["regular_staff", "staff_admin", "super_staff_admin"],
        "departments": ["food_and_beverage"],
        "roles": [
            "banquet_manager",
            "bar_manager",
            "bar_staff",
            "commis_waiter",
            "food_and_beverage_manager",
            "food_runner",
            "head_waiter",
            "manager",
            "room_service_waiter",
            "waiter",
        ],
    },
    "front_office_panel": {
        "access_levels": ["regular_staff", "staff_admin", "super_staff_admin"],
        "departments": ["front_office"],
        "roles": [
            "concierge",
            "front_office_manager",
            "guest_relations_officer",
            "porter",
            "receptionist",
            "reservation_agent",
        ],
    },
    "kitchen_panel": {
        "access_levels": ["regular_staff", "staff_admin", "super_staff_admin"],
        "departments": ["kitchen"],
        "roles": [
            "head_chef",
            "kitchen_helper",
            "line_cook",
            "pastry_chef",
            "prep_cook",
            "sous_chef",
        ],
    },
    "leisure_panel": {
        "access_levels": ["regular_staff", "staff_admin", "super_staff_admin"],
        "departments": ["leisure"],
        "roles": [
            "fitness_instructor",
            "lifeguard",
            "recreation_coordinator",
            "spa_manager",
            "wellness_coach",
        ],
    },
    "maintenance_panel": {
        "access_levels": ["regular_staff", "staff_admin", "super_staff_admin"],
        "departments": ["maintenance"],
        "roles": [
            "electrician",
            "general_maintenance_worker",
            "hvac_technician",
            "maintenance_manager",
            "plumber",
        ],
    },
    "management_panel": {
        "access_levels": ["staff_admin", "super_staff_admin"],  # only admins
        "departments": ["management"],
        "roles": [
            "deputy_manager",
            "duty_manager",
            "finance_director",
            "general_manager",
            "marketing_manager",
            "sales_manager",
        ],
    },
    "security_panel": {
        "access_levels": ["staff_admin", "super_staff_admin"],  # only admins
        "departments": ["security"],
        "roles": [
            "access_control_officer",
            "emergency_response_coordinator",
            "loss_prevention_officer",
            "security_manager",
            "security_officer",
        ],
    },
}


class Permissions:
    @staticmethod
    def has_access(staff: Staff, nav_key: str) -> bool:
        """
        Check if the given staff has access to the specified navigation panel.
        """
        config = NAV_ACCESS_RULES.get(nav_key)
        if not config:
            return False

        if staff.access_level not in config["access_levels"]:
            return False

        if not staff.department or staff.department.slug not in config["departments"]:
            return False

        if not staff.role or staff.role.slug not in config["roles"]:
            return False

        return True

    @staticmethod
    def get_accessible_navs(staff: Staff):
        """
        Return a list of all nav keys accessible by the staff.
        """
        return [nav for nav in NAV_ACCESS_RULES if Permissions.has_access(staff, nav)]
