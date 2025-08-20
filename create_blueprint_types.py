import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()

from bookings.models import BlueprintObjectType  # Adjust app name if needed

# Define blueprint types
blueprint_types_data = {
    "entrance": {
        "icon": "door-open",
        "default_width": 50,
        "default_height": 100,
    },
    "window": {
        "icon": "window-restore",
        "default_width": 60,
        "default_height": 40,
    },
    "till": {
        "icon": "cash-register",
        "default_width": 40,
        "default_height": 40,
    },
    "decor": {
        "icon": "star",
        "default_width": 30,
        "default_height": 30,
    },
    "exit": {
        "icon": "sign-out-alt",
        "default_width": 50,
        "default_height": 100,
    },
    "couch": {
        "icon": "couch",
        "default_width": 120,
        "default_height": 60,
    },
    "chair": {
        "icon": "chair",
        "default_width": 40,
        "default_height": 40,
    },
    "table": {
        "icon": "table",
        "default_width": 80,
        "default_height": 50,
    },
    "bed": {
        "icon": "bed",
        "default_width": 100,
        "default_height": 60,
    },
}

def create_blueprint_types():
    for type_slug, attrs in blueprint_types_data.items():
        type_name = type_slug.replace('-', ' ').title()
        obj_type, created = BlueprintObjectType.objects.get_or_create(
            name=type_name,
            defaults={
                "icon": attrs.get("icon", ""),
                "default_width": attrs.get("default_width", 50),
                "default_height": attrs.get("default_height", 50),
            }
        )
        if not created:
            # Optionally update attributes if the type already exists
            updated = False
            for field in ["icon", "default_width", "default_height"]:
                if getattr(obj_type, field) != attrs.get(field, getattr(obj_type, field)):
                    setattr(obj_type, field, attrs[field])
                    updated = True
            if updated:
                obj_type.save()
                print(f"Updated BlueprintObjectType '{type_name}'")
            else:
                print(f"BlueprintObjectType '{type_name}' already exists")
        else:
            print(f"Created BlueprintObjectType '{type_name}'")

if __name__ == "__main__":
    create_blueprint_types()
    print("Blueprint type creation process completed.")
