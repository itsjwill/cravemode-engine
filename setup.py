"""
CraveMode Engine — One-time setup.

1. Checks API credentials
2. Creates CraveMode table in Airtable
3. Verifies provider connectivity
"""

import sys
import os

# Add parent for provider access
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.config import check_credentials, GOOGLE_API_KEY, AIRTABLE_BASE_ID
from tools.airtable import create_cravemode_table


def main():
    print("=" * 50)
    print("  CraveMode Engine Setup")
    print("=" * 50)

    # Step 1: Check credentials
    print("\n[1/3] Checking API credentials...")
    missing = check_credentials()
    if missing:
        print("\nSetup cannot continue. Add missing keys to .claude/.env")
        return False

    print("All credentials configured.")

    # Step 2: Create Airtable table
    print(f"\n[2/3] Creating CraveMode table (base: {AIRTABLE_BASE_ID})...")
    try:
        create_cravemode_table()
    except Exception as e:
        print(f"Error creating table: {e}")
        return False

    # Step 3: Verify Google API
    print("\n[3/3] Verifying Google AI Studio connection...")
    if GOOGLE_API_KEY:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GOOGLE_API_KEY}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                image_models = [m["name"] for m in models if "image" in m.get("name", "").lower() or "nano" in m.get("name", "").lower()]
                print(f"Connected. {len(models)} models available.")
            else:
                print(f"Warning: API returned {resp.status_code}")
        except Exception as e:
            print(f"Warning: Could not reach Google AI Studio: {e}")
    else:
        print("Skipped (no GOOGLE_API_KEY)")

    print("\n" + "=" * 50)
    print("  CraveMode Engine ready!")
    print("=" * 50)
    print(f"\nBase ID: {AIRTABLE_BASE_ID}")
    print("Table: CraveMode")
    print("\nNext steps:")
    print("  1. Add restaurant photos to cravemode/references/inputs/")
    print("  2. Register a client:")
    print('     from tools.client_manager import create_client')
    print('     create_client("marios-pizza", "Mario\'s Pizza", "italian", "starter")')
    print("  3. Generate a content plan:")
    print('     from tools.food_prompts import generate_content_plan')
    print('     plan = generate_content_plan("Mario\'s Pizza", dishes, "italian", "starter")')
    print("  4. Create records in Airtable:")
    print('     from tools.airtable import create_content_plan')
    print('     create_content_plan(plan)')

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
