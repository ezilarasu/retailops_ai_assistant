import json
from pathlib import Path

import pandas as pd
from langchain_core.tools import tool


DATA_DIR = Path("data")


@tool
def get_low_stock_items(store_id: str) -> str:
    """
    Get low-stock inventory items for a store.

    A low-stock item is one where on_hand is less than reorder_point.
    Requires:
    - store_id

    If the user does not provide a store_id, ask the user which store they want to check.
    """
    try:
        inventory_path = DATA_DIR / "inventory.csv"
        df = pd.read_csv(inventory_path)

        store_df = df[df["store_id"].astype(str) == str(store_id)]

        low_stock_df = store_df[
            store_df["on_hand"] < store_df["reorder_point"]
        ]

        if low_stock_df.empty:
            return f"No low-stock items found for store {store_id}."

        records = low_stock_df.to_dict(orient="records")

        return json.dumps(records, indent=2)
    except Exception:
        return f"Unable to retrieve low-stock items for store {store_id}."    

@tool
def get_vendor_for_sku(sku: str) -> str:
    """
    Get vendor contact details for a product SKU.
    """
    try:
        inventory_path = DATA_DIR / "inventory.csv"
        vendors_path = DATA_DIR / "vendors.csv"

        inventory_df = pd.read_csv(inventory_path)
        vendors_df = pd.read_csv(vendors_path)

        sku_rows = inventory_df[
            inventory_df["sku"].str.upper() == sku.upper()
        ]

        if sku_rows.empty:
            return f"No inventory item found for SKU {sku}."

        vendor_id = sku_rows.iloc[0]["vendor_id"]

        vendor_rows = vendors_df[
            vendors_df["vendor_id"] == vendor_id
        ]

        if vendor_rows.empty:
            return f"No vendor found for vendor_id {vendor_id}."

        record = vendor_rows.iloc[0].to_dict()

        return json.dumps(record, indent=2)
    except Exception:
        return f"Unable to retrieve vendor details for SKU {sku}."


@tool
def get_open_incidents(store_id: str) -> str:
    """
    Get open or in-progress incidents for a store.
    """
    try:
        incidents_path = DATA_DIR / "incidents.json"

        with open(incidents_path, "r") as file:
            incidents = json.load(file)

        results = [
            incident
            for incident in incidents
            if str(incident["store_id"]) == str(store_id)
            and incident["status"] in ["open", "in_progress"]
        ]

        if not results:
            return f"No open or in-progress incidents found for store {store_id}."

        return json.dumps(results, indent=2)
    except Exception:
        return f"Unable to retrieve open or in-progress incidents for store {store_id}."


tools = [
    get_low_stock_items,
    get_vendor_for_sku,
    get_open_incidents,
]

def get_tools():
    return [
        get_low_stock_items,
        get_vendor_for_sku,
        get_open_incidents,
    ]