USERNAME_MAX_LENGTH = 50


def normalize_username(username: str) -> str:
    normalized = username.strip()
    if not normalized or len(normalized) > USERNAME_MAX_LENGTH:
        raise ValueError(
            f"El usuario debe tener entre 1 y {USERNAME_MAX_LENGTH} caracteres."
        )
    return normalized
