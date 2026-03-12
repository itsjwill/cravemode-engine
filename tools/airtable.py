"""
CraveMode Airtable Operations.

Works with the existing "Leads" table in the n32 | Restaurant Photography base.

Existing schema (from Airtable):
  Name, Category, Address, Completed_At, Website, Instagram,
  input_image, Status, Prompt, image_1, image_2,
  Video_Status, transition_prompt, video

Status values: Create, Done, Skip

FIELD MAPPING:
  The parent creative-engine-template uses "Content" table field names
  (Image Prompt, Generated Image 1, etc.). CraveMode's Leads table uses
  different names (Prompt, image_1, etc.). The adapter functions below
  translate between the two so the parent's image_gen.py and video_gen.py
  work seamlessly with the Leads table.
"""

import requests
from . import config


# --- Field Mapping ---
# Maps CraveMode Leads table fields <-> parent Content table fields

FIELD_MAP = {
    "restaurant_name": "Name",
    "cuisine": "Category",
    "address": "Address",
    "website": "Website",
    "instagram": "Instagram",
    "input_image": "input_image",
    "status": "Status",
    "image_prompt": "Prompt",
    "generated_image_1": "image_1",
    "generated_image_2": "image_2",
    "video_status": "Video_Status",
    "video_prompt": "transition_prompt",
    "generated_video": "video",
}

# Parent field name -> Leads field name (for reading records)
_LEADS_TO_PARENT = {
    "Name": "Ad Name",
    "Prompt": "Image Prompt",
    "image_1": "Generated Image 1",
    "image_2": "Generated Image 2",
    "Status": "Image Status",
    "Video_Status": "Video Status",
    "transition_prompt": "Video Prompt",
    "video": "Generated Video 1",
    "input_image": "Reference Images",
    "Category": "Product",
}

# Parent field name -> Leads field name (for writing updates)
_PARENT_TO_LEADS = {v: k for k, v in _LEADS_TO_PARENT.items()}


def _headers():
    """Standard Airtable API headers."""
    return {
        "Authorization": f"Bearer {config.AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }


# --- Field Adapters ---
# Translate between Leads table fields and parent Content table fields
# so parent's image_gen.py / video_gen.py work with our Leads table.

def adapt_record_for_parent(record):
    """
    Adapt a Leads table record so it looks like a Content table record.
    The parent's image_gen.py expects fields like "Image Prompt", "Ad Name", etc.
    """
    fields = record.get("fields", {})
    adapted_fields = dict(fields)  # Keep all original fields

    for leads_field, parent_field in _LEADS_TO_PARENT.items():
        if leads_field in fields and parent_field not in adapted_fields:
            adapted_fields[parent_field] = fields[leads_field]

    return {"id": record["id"], "fields": adapted_fields}


def adapt_records_for_parent(records):
    """Adapt multiple Leads records for the parent engine."""
    return [adapt_record_for_parent(r) for r in records]


def adapt_update_for_leads(parent_fields):
    """
    Translate a parent-style update dict back to Leads field names.
    e.g., {"Generated Image 1": [...]} -> {"image_1": [...]}
    """
    leads_fields = {}
    for key, value in parent_fields.items():
        leads_key = _PARENT_TO_LEADS.get(key, key)
        leads_fields[leads_key] = value
    return leads_fields


def _table_url():
    """Base URL for the Leads table."""
    return f"{config.AIRTABLE_API_URL}/{config.AIRTABLE_BASE_ID}/{config.AIRTABLE_TABLE_NAME}"


# --- Table Setup ---

def create_cravemode_table():
    """
    Verify the Leads table exists and has the required fields.
    The Leads table is pre-existing in the n32 | Restaurant Photography base.
    This function validates connectivity and field availability.

    Unlike the parent's create_ugc_table() which creates a new table,
    CraveMode reuses an existing table — so we just verify it works.
    """
    print(f"Checking Leads table in base {config.AIRTABLE_BASE_ID}...")

    # Verify we can read from the table
    try:
        records = get_records()
        total = len(records)

        # Count by status
        by_status = {}
        for r in records:
            status = r.get("fields", {}).get("Status", "Unknown")
            by_status[status] = by_status.get(status, 0) + 1

        print(f"  Table: {config.AIRTABLE_TABLE_NAME}")
        print(f"  Records: {total}")
        for status, count in sorted(by_status.items()):
            print(f"    {status}: {count}")

        # Verify key fields exist by checking first record
        if records:
            fields = records[0].get("fields", {})
            expected = ["Name", "Status", "Prompt", "input_image"]
            missing = [f for f in expected if f not in fields]
            if missing:
                print(f"  WARNING: Fields not found in first record: {missing}")
                print(f"  (They may exist but be empty — check Airtable)")
            else:
                print(f"  All required fields verified.")

        return {"table": config.AIRTABLE_TABLE_NAME, "records": total, "by_status": by_status}

    except Exception as e:
        raise Exception(
            f"Cannot access Leads table. Verify AIRTABLE_API_KEY and AIRTABLE_BASE_ID "
            f"in .claude/.env. Error: {e}"
        )


# --- Record CRUD ---

def create_record(fields):
    """Create a single record."""
    response = requests.post(_table_url(), headers=_headers(), json={"fields": fields})
    if response.status_code != 200:
        raise Exception(f"Airtable create failed: {response.text}")
    return response.json()


def create_records_batch(records_fields):
    """Create multiple records in batches of 10."""
    all_created = []
    for i in range(0, len(records_fields), 10):
        batch = records_fields[i : i + 10]
        records = [{"fields": f} for f in batch]
        response = requests.post(_table_url(), headers=_headers(), json={"records": records})
        if response.status_code != 200:
            raise Exception(f"Airtable batch create failed (batch {i}): {response.text}")
        created = response.json().get("records", [])
        all_created.extend(created)
        print(f"Created {len(all_created)}/{len(records_fields)} records")
    return all_created


def get_records(filter_formula=None):
    """Get records with optional Airtable formula filter. Handles pagination."""
    params = {}
    if filter_formula:
        params["filterByFormula"] = filter_formula

    all_records = []
    offset = None

    while True:
        if offset:
            params["offset"] = offset
        response = requests.get(_table_url(), headers=_headers(), params=params)
        if response.status_code != 200:
            raise Exception(f"Airtable query failed: {response.text}")
        data = response.json()
        all_records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break

    return all_records


def update_record(record_id, fields):
    """Update a single record."""
    url = f"{_table_url()}/{record_id}"
    response = requests.patch(url, headers=_headers(), json={"fields": fields})
    if response.status_code != 200:
        raise Exception(f"Airtable update failed: {response.text}")
    return response.json()


# --- CraveMode Convenience Queries ---

def get_pending_images():
    """Get records with Status = 'Create' (ready for image generation)."""
    return get_records('{Status} = "Create"')


def get_completed():
    """Get records with Status = 'Done'."""
    return get_records('{Status} = "Done"')


def get_skipped():
    """Get records with Status = 'Skip'."""
    return get_records('{Status} = "Skip"')


def get_records_by_restaurant(restaurant_name):
    """Get all records for a specific restaurant."""
    return get_records(f'{{Name}} = "{restaurant_name}"')


def get_records_by_category(category):
    """Get all records of a cuisine/category (e.g., 'Italian restaurant')."""
    return get_records(f'{{Category}} = "{category}"')


def get_records_with_images():
    """Get records that have generated images."""
    return get_records('NOT({image_1} = "")')


def get_records_needing_video():
    """Get records with images but no video yet."""
    return get_records('AND(NOT({image_1} = ""), {video} = "")')


def get_all_restaurants():
    """Get all records, returns full dataset."""
    return get_records()


# --- Portfolio / Showcase ---

def get_showcase_records(limit=10):
    """
    Get the best completed records for portfolio/demo purposes.
    Returns Done records that have images and videos.
    """
    records = get_records('AND({Status} = "Done", NOT({image_1} = ""), NOT({video} = ""))')
    return records[:limit]


def get_restaurant_summary():
    """
    Get a summary of all restaurants in the base.

    Returns:
        dict: {"total": int, "by_status": {...}, "by_category": {...}}
    """
    all_records = get_records()

    by_status = {}
    by_category = {}

    for r in all_records:
        f = r.get("fields", {})
        status = f.get("Status", "Unknown")
        category = f.get("Category", "Unknown")

        by_status[status] = by_status.get(status, 0) + 1
        by_category[category] = by_category.get(category, 0) + 1

    return {
        "total": len(all_records),
        "by_status": by_status,
        "by_category": by_category,
    }
