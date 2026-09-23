import random
import string


def generate_tag(length: int = 6) -> str:
    if length < 1:
        raise ValueError("length must be >= 1")
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_tags(count: int = 2, length: int = 6) -> list[str]:
    if count < 0:
        raise ValueError("count must be >= 0")
    return [generate_tag(length) for _ in range(count)]


def generate_test_paste(
    content_length: int = 32,
    tag_count: int = 2,
    tag_length: int = 6,
    is_private: bool = False,
) -> dict:
    if content_length == 0:
        content = ""
    else:
        content = ''.join(random.choices(string.ascii_letters + string.digits + " ", k=content_length))
    return {
        "content": content.strip(),
        "is_private": is_private,
        "tags": generate_tags(tag_count, tag_length),
    }
