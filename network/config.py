import yaml

def load_config(path: str = "config.yaml") -> dict:
    """Wczytuje konfigurację z pliku YAML."""
    with open(path, 'r') as file:
        return yaml.safe_load(file)