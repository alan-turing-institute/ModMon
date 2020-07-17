import configparser
from pathlib import Path
import warnings

config = configparser.ConfigParser()

# search for .modmon.ini in home directory, if not present use defaults.ini
user_config_path = Path(Path.home(), ".modmom.ini")
default_config_path = Path(Path(__file__).parent, "defaults.ini")

if user_config_path.exists():
    config_path = user_config_path
elif default_config_path.exists():
    config_path = default_config_path
else:
    raise FileNotFoundError(
        f"Could not find ModMon configuration file at {user_config_path} or "
        f"{default_config_path}"
    )

with open(config_path, "r") as f:
    config.read_file(f)

if "database" not in config:
    raise KeyError(f"[database] section not found in {config_path}")
if "database-admin" not in config:
    raise warnings.warn(
        f"[database-admin] not found in {config_path}: "
        "Creating or deleting the database will fail."
    )
