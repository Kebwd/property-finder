import json
from difflib import get_close_matches
from key_library import KEY_MAP
import yaml

def load_sample(json_path):
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    # Flatten payload to a single sample record
    if isinstance(data, dict):
        for key in ["data", "results", "transactions", "items"]:
            if key in data:
                return data[key][0]  # first row
        return next(iter(data.values()))  # fallback
    elif isinstance(data, list):
        return data[0]

def suggest_field_mapping(sample_row):
    suggestions = {}
    for std_field, known_aliases in KEY_MAP.items():
        candidates = get_close_matches(std_field, sample_row.keys(), n=3, cutoff=0.5)
        if candidates:
            suggestions[std_field] = candidates[0]  # best match
        else:
            # fallback: find keys that exist in known aliases
            match = [k for k in sample_row if k in known_aliases]
            if match:
                suggestions[std_field] = match[0]
    return suggestions

def generate_yaml_config(name, start_url, suggestions):
    config = {
        "name": name,
        "type": "store",
        "start_url": start_url,
        "pagination": {
            "data_key": "",  # fill manually
            "cursor_key": "",
            "cursor_param": "&cursor="
        },
        "fields": suggestions,
        "filters": {
            "tx_type": "tx_type",
            "tx_type_value": "S",
            "match_today": True
        }
    }
    yaml_path = f"config/{name}.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True)
    print(f"Draft config saved to {yaml_path}")