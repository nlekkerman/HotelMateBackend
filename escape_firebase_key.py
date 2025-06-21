import json

# Replace this path with your actual JSON file path if different
json_file_path = "hotel-mate-d878f-07c59aad1fb8.json"

try:
    with open(json_file_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Properly escape the private_key
    raw["private_key"] = raw["private_key"].replace("\n", "\\n")

    # Output Heroku-compatible one-line JSON
    print(json.dumps(raw))
except Exception as e:
    print(f"❌ Something went wrong: {e}")
