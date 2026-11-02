from app.tools import (
    get_low_stock_items,
    get_vendor_for_sku,
    get_open_incidents,
)


print("\nLow-stock items for store 102:")
print(get_low_stock_items.invoke({"store_id": "102"}))

print("\nVendor for SKU DENIM-4421:")
print(get_vendor_for_sku.invoke({"sku": "DENIM-4421"}))

print("\nOpen incidents for store 102:")
print(get_open_incidents.invoke({"store_id": "102"}))