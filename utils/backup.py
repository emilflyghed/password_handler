import json
import os
import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from database.models import get_all_entries, add_entry
from config import NONCE_LENGTH


def export_backup(conn, key: bytes, filepath: str) -> None:
    entries = get_all_entries(conn, key)
    # Strip id and timestamps for portability
    data = [
        {"service": e["service"], "username": e["username"], "password": e["password"]}
        for e in entries
    ]
    payload = json.dumps(data).encode()

    nonce = os.urandom(NONCE_LENGTH)
    aesgcm = AESGCM(bytes(key))
    ciphertext = aesgcm.encrypt(nonce, payload, None)

    with open(filepath, "wb") as f:
        f.write(nonce + ciphertext)


def import_backup(conn, key: bytes, filepath: str) -> int:
    with open(filepath, "rb") as f:
        raw = f.read()

    nonce = raw[:NONCE_LENGTH]
    ciphertext = raw[NONCE_LENGTH:]

    aesgcm = AESGCM(bytes(key))
    payload = aesgcm.decrypt(nonce, ciphertext, None)
    entries = json.loads(payload.decode())

    count = 0
    for e in entries:
        add_entry(conn, key, e["service"], e["username"], e["password"])
        count += 1
    return count
