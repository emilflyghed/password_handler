import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from crypto.encryption import generate_salt, derive_key, zero_key
from database.models import get_all_entries, add_entry
from config import NONCE_LENGTH, SALT_LENGTH


# Backup file layout:
#   [32 bytes salt][12 bytes nonce][ciphertext...]
# The salt lets the importer re-derive the export key from the original PIN.


def export_backup(conn, key: bytes, pin: str, filepath: str) -> None:
    entries = get_all_entries(conn, key)
    data = [
        {"service": e["service"], "username": e["username"], "password": e["password"]}
        for e in entries
    ]
    payload = json.dumps(data).encode()

    salt = generate_salt()
    export_key = derive_key(pin, salt)

    nonce = os.urandom(NONCE_LENGTH)
    aesgcm = AESGCM(bytes(export_key))
    ciphertext = aesgcm.encrypt(nonce, payload, None)
    zero_key(export_key)

    with open(filepath, "wb") as f:
        f.write(salt + nonce + ciphertext)


def import_backup(conn, key: bytes, pin: str, filepath: str) -> int:
    with open(filepath, "rb") as f:
        raw = f.read()

    salt = raw[:SALT_LENGTH]
    nonce = raw[SALT_LENGTH:SALT_LENGTH + NONCE_LENGTH]
    ciphertext = raw[SALT_LENGTH + NONCE_LENGTH:]

    import_key = derive_key(pin, salt)
    aesgcm = AESGCM(bytes(import_key))
    payload = aesgcm.decrypt(nonce, ciphertext, None)
    zero_key(import_key)

    entries = json.loads(payload.decode())

    count = 0
    for e in entries:
        add_entry(conn, key, e["service"], e["username"], e["password"])
        count += 1
    return count
