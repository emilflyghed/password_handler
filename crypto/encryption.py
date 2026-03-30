import os
import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend

from config import (
    SCRYPT_N, SCRYPT_R, SCRYPT_P,
    SALT_LENGTH, AES_KEY_LENGTH, NONCE_LENGTH,
)


def generate_salt() -> bytes:
    return os.urandom(SALT_LENGTH)


def derive_key(pin: str, salt: bytes) -> bytearray:
    kdf = Scrypt(
        salt=salt,
        length=AES_KEY_LENGTH,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        backend=default_backend(),
    )
    key = kdf.derive(pin.encode())
    return bytearray(key)


def encrypt(plaintext: str, key: bytes) -> str:
    nonce = os.urandom(NONCE_LENGTH)
    aesgcm = AESGCM(bytes(key))
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()


def decrypt(encrypted_b64: str, key: bytes) -> str:
    raw = base64.b64decode(encrypted_b64)
    nonce = raw[:NONCE_LENGTH]
    ciphertext = raw[NONCE_LENGTH:]
    aesgcm = AESGCM(bytes(key))
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode()


def zero_key(key: bytearray) -> None:
    for i in range(len(key)):
        key[i] = 0
