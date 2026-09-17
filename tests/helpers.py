import hashlib


def sid(label: str) -> str:
    """Turn a short readable label into a deterministic UUID-shaped session id."""
    digest = hashlib.md5(label.encode()).hexdigest()
    return f"{digest[0:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"
