import string
import secrets


def generate_short_code(length: int = 7) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))
