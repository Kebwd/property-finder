config_map={
  "province": [],
  "city": [],
  "country": [],
  "town": [],
  "street": ["street_name_zh"],
  "road": [],
  "type": ["ics_type","propertyUsageDisplayName"],
  "estate_name_zh": [],
  "flat": ["flat",],
  "building_name_zh": ["building_name_zh","propertyNameCn"],
  "floor": ["floor_zh","floor"],
  "unit": ["unit"],
  "area": ["area","transactionArea"],
  "house_type": [],
  "deal_date": ["tx_date","transactionDate"],
  "deal_price": ["sell","price"],
  "developer": ["developer"]
}
def extract_with_fallback(obj: dict, keys: list) -> any:
    """
    Given a JSON object and a list of possible keys,
    return the first non-empty value found, or None.
    """
    for key in keys:
        val = obj.get(key)
        if val not in (None, "", []):
            return val
    return None