import sys
from pathlib import Path

# Paths — when bundled as .exe, store data next to the .exe, not in the temp dir
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

DB_DIR = BASE_DIR / "data"
DB_PATH = DB_DIR / "vault.db"

# Crypto
SCRYPT_N = 2**17
SCRYPT_R = 8
SCRYPT_P = 1
SALT_LENGTH = 32
AES_KEY_LENGTH = 32
NONCE_LENGTH = 12
VERIFICATION_TOKEN = "VAULT_VERIFIED"

# PIN
PIN_MIN_LENGTH = 6
PIN_MAX_LENGTH = 8

# App behavior
CLIPBOARD_CLEAR_SECONDS = 15
AUTO_LOCK_SECONDS = 30
PASSWORD_SHOW_SECONDS = 5

# GUI
APP_TITLE = "Password Vault"
APP_SIZE = "950x600"
APP_MIN_SIZE = (750, 500)
DEFAULT_THEME = "dark"

# Backup
BACKUP_EXTENSION = ".vault"
