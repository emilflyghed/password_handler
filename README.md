# Password Vault

A desktop password manager built with Python that encrypts all stored credentials using AES-256-GCM. Authentication is handled via a numeric PIN that derives the encryption key through scrypt, meaning no master password or key file is ever stored on disk.

## Architecture

```
password_handler/
├── main.pyw              # Entry point — launches the CTk application
├── config.py             # Centralized constants (crypto params, timers, GUI sizing)
├── crypto/
│   ├── encryption.py     # Key derivation (scrypt), AES-256-GCM encrypt/decrypt, key zeroing
│   └── generator.py      # Cryptographically secure password generation (secrets module)
├── database/
│   ├── db.py             # SQLite connection factory and schema initialization
│   └── models.py         # CRUD operations — all fields encrypted before write
├── gui/
│   ├── app.py            # Root CTk window, auto-lock timer, frame management
│   ├── login_frame.py    # PIN creation/verification screen with brute-force lockout
│   ├── main_frame.py     # Vault entry list, search, toolbar, import/export controls
│   ├── entry_dialog.py   # Add/edit credential dialog with inline generator access
│   └── generator_dialog.py  # Configurable password generator with live preview
├── utils/
│   ├── clipboard.py      # Copy-to-clipboard with timed auto-clear
│   └── backup.py         # AES-256-GCM encrypted backup export/import (.vault files)
├── data/
│   └── vault.db          # SQLite database (all sensitive columns are ciphertext)
├── build.bat             # PyInstaller build script
├── PasswordVault.spec    # PyInstaller spec (one-file, windowed, icon)
└── requirements.txt
```

## Tech Stack

| Component       | Technology                         |
|-----------------|------------------------------------|
| Language        | Python 3.12+                       |
| GUI Framework   | CustomTkinter 5.2+                 |
| Encryption      | `cryptography` — AES-256-GCM      |
| Key Derivation  | scrypt (N=2^17, r=8, p=1)         |
| Storage         | SQLite 3 (via stdlib `sqlite3`)    |
| RNG             | `secrets` (CSPRNG)                 |
| Packaging       | PyInstaller (single-file `.exe`)   |

## Cryptographic Design

### Key Derivation

The user's numeric PIN (6–8 digits) is fed into **scrypt** with a 32-byte random salt to produce a 256-bit AES key. The scrypt parameters (`N=131072, r=8, p=1`) make brute-force attacks computationally expensive — approximately 57 ms per attempt, making exhaustive search of the 6-digit PIN space take ~16 hours on a single core.

The salt is stored in the `config` table of the SQLite database. The derived key is **never persisted**; it exists only in memory as a `bytearray` and is explicitly zeroed (`zero_key()`) on lock or application exit.

### Encryption

All sensitive fields (service name, username, password) are encrypted individually using **AES-256-GCM** before being written to the database. Each encryption operation generates a fresh 12-byte nonce. The nonce is prepended to the ciphertext and the combined blob is base64-encoded for storage.

GCM mode provides both confidentiality and integrity — any tampering with stored ciphertext will cause decryption to fail with an authentication error.

### PIN Verification

On first run, the app encrypts a known token (`VAULT_VERIFIED`) with the derived key and stores the ciphertext as `pin_verifier` in the `config` table. On subsequent logins, the entered PIN derives a key and attempts to decrypt the verifier. A successful decryption that yields the expected token confirms the PIN is correct.

### Backup Format

Exported `.vault` files contain all vault entries as a JSON payload encrypted with AES-256-GCM using the current session key. The file format is: `[12-byte nonce][ciphertext]` (raw binary). Backups can only be imported with the same PIN that created them.

## Security Features

- **Brute-force protection**: After 3 failed PIN attempts, an escalating lockout timer activates (30s × (attempts − 2)).
- **Auto-lock**: The vault locks after 30 seconds of inactivity (no mouse, keyboard, or click events). All open dialogs are destroyed and the key is zeroed from memory.
- **Clipboard auto-clear**: Copied passwords are automatically cleared from the system clipboard after 15 seconds.
- **Password visibility timeout**: Revealed passwords in the entry list are automatically re-masked after 5 seconds.
- **Key zeroing**: The encryption key (`bytearray`) is overwritten with zeros on lock, exit, and session termination to minimize exposure in memory.

## Password Generator

The built-in generator uses Python's `secrets` module (CSPRNG) and supports:

- Configurable length (8–64 characters)
- Toggleable character classes: uppercase, lowercase, digits, symbols (`!@#$%^&*()-_=+[]{}|;:,.<>?`)
- Optional exclusion of ambiguous characters (`0, O, 1, l, I, |`)
- Guaranteed representation from each enabled character class via Fisher-Yates shuffle

Generated passwords can be copied to clipboard or inserted directly into the entry form.

## Database Schema

```sql
CREATE TABLE config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE entries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    service    TEXT NOT NULL,   -- AES-256-GCM ciphertext (base64)
    username   TEXT NOT NULL,   -- AES-256-GCM ciphertext (base64)
    password   TEXT NOT NULL,   -- AES-256-GCM ciphertext (base64)
    created_at TEXT NOT NULL,   -- ISO 8601 UTC timestamp
    updated_at TEXT NOT NULL    -- ISO 8601 UTC timestamp
);
```

The `config` table stores the scrypt salt (hex-encoded) and the PIN verifier (base64-encoded ciphertext). Timestamps are stored in plaintext since they do not contain sensitive information.

## Installation & Usage

```bash
pip install -r requirements.txt
python main.pyw
```

### Requirements

- `customtkinter>=5.2.0`
- `cryptography>=42.0.0`

### Building a Standalone Executable

```bash
# Windows
build.bat
# Output: dist/PasswordVault.exe
```

The PyInstaller build produces a single-file windowed executable. The `data/` directory (containing `vault.db`) is created next to the `.exe` at runtime.

## Configuration

All tunable parameters are defined in `config.py`:

| Constant                 | Default      | Description                              |
|--------------------------|--------------|------------------------------------------|
| `SCRYPT_N`               | 2^17         | scrypt CPU/memory cost parameter         |
| `SCRYPT_R`               | 8            | scrypt block size                        |
| `SCRYPT_P`               | 1            | scrypt parallelization                   |
| `SALT_LENGTH`            | 32 bytes     | Random salt length for key derivation    |
| `AES_KEY_LENGTH`         | 32 bytes     | AES-256 key size                         |
| `NONCE_LENGTH`           | 12 bytes     | GCM nonce size                           |
| `PIN_MIN_LENGTH`         | 6            | Minimum PIN digits                       |
| `PIN_MAX_LENGTH`         | 8            | Maximum PIN digits                       |
| `CLIPBOARD_CLEAR_SECONDS`| 15          | Seconds before clipboard auto-clear      |
| `AUTO_LOCK_SECONDS`      | 30           | Idle seconds before vault auto-locks     |
| `PASSWORD_SHOW_SECONDS`  | 5            | Seconds before password re-masks         |
