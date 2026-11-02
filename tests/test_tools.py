from app.tools import (
    get_low_stock_items,
    get_vendor_for_sku,
    get_open_incidents,
)


def test_get_low_stock_items_returns_string():
    result = get_low_stock_items.invoke({"store_id": "102"})
    assert isinstance(result, str)
    assert "DENIM-4421" in result


def test_get_vendor_for_sku_returns_string():
    result = get_vendor_for_sku.invoke({"sku": "DENIM-4421"})
    assert isinstance(result, str)
    assert "BlueRiver Denim Supply" in result


def test_get_open_incidents_returns_string():
    result = get_open_incidents.invoke({"store_id": "102"})
    assert isinstance(result, str)
    assert "INC-1001" in result