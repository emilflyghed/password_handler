import secrets
import string


def generate_password(
    length: int = 16,
    uppercase: bool = True,
    lowercase: bool = True,
    digits: bool = True,
    symbols: bool = True,
    exclude_ambiguous: bool = False,
) -> str:
    pools = []
    if uppercase:
        pools.append(string.ascii_uppercase)
    if lowercase:
        pools.append(string.ascii_lowercase)
    if digits:
        pools.append(string.digits)
    if symbols:
        pools.append("!@#$%^&*()-_=+[]{}|;:,.<>?")

    if not pools:
        pools.append(string.ascii_letters + string.digits)

    combined = "".join(pools)

    if exclude_ambiguous:
        ambiguous = set("0O1lI|")
        combined = "".join(c for c in combined if c not in ambiguous)

    # Guarantee at least one char from each enabled pool
    password_chars = [secrets.choice(pool) for pool in pools]

    # Fill remaining length
    remaining = length - len(password_chars)
    for _ in range(max(0, remaining)):
        password_chars.append(secrets.choice(combined))

    # Shuffle to avoid predictable positions
    result = list(password_chars)
    for i in range(len(result) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        result[i], result[j] = result[j], result[i]

    return "".join(result)
