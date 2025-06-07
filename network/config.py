import yaml

def load_config(path="config.yaml"):
    """
    Ładuje konfigurację z pliku YAML.
    """
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)