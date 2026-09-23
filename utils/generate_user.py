import random
import string

SPECIAL_CHARS = "@$!%*?&"
ALLOWED_CHARS = string.ascii_letters + string.digits + SPECIAL_CHARS


def generate_username(length: int = 10) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_email(username: str | None = None) -> str:
    username = username or generate_username(8)
    domain = random.choice(["example.com", "test.com", "mail.com"])
    return f"{username}@{domain}"


def generate_password(length: int = 12) -> str:
    if length < 4:
        raise ValueError("length must be >= 4")
    required = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice(SPECIAL_CHARS),
    ]
    filler = [random.choice(ALLOWED_CHARS) for _ in range(length - 4)]
    chars = required + filler
    random.shuffle(chars)
    return ''.join(chars)


def generate_test_user() -> dict:
    username = generate_username()
    return {
        "username": username,
        "email": generate_email(username),
        "password": generate_password(),
    }