import yaml
import os
from pathlib import Path

def load_config(path, source=None):
    with open(path, "r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)

    configs = raw_config.get("config", [])
    if not isinstance(configs, list):
        raise ValueError(f"'config' must be a list in {path}")

    required_keys = ["zone", "type", "start_urls", "fields", "xpaths"]

    filtered_configs = []
    for idx, cfg in enumerate(configs):
        if source and cfg.get("source") != source:
            continue

        missing_keys = [key for key in required_keys if key not in cfg]
        if missing_keys:
            raise ValueError(
                f"Missing required keys {missing_keys} in config block #{idx+1} in file {path}"
            )

        filtered_configs.append(cfg)

    if source and not filtered_configs:
        raise ValueError(f"No config found for source '{source}' in {path}")

    return filtered_configs

def load_mapping_config(path):
    """
    Load a YAML mapping file (e.g. type_mapping.yaml or key_mapping.yaml)
    and return its contents as a dict.
    """
    fp = Path(path)
    if not fp.exists():
        raise FileNotFoundError(f"Mapping file not found: {path}")
    data = yaml.safe_load(fp.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict in mapping file {path}, got {type(data)}")
    return data