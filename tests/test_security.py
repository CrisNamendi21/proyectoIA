from app.core.security import hash_password, verify_password


def test_password_hash_accepts_only_the_matching_password() -> None:
    password = "clave-ficticia-para-prueba-2026"

    stored_hash = hash_password(password)

    assert stored_hash.startswith("$argon2id$")
    assert stored_hash != password
    assert password not in stored_hash
    assert verify_password(password, stored_hash)
    assert not verify_password("otra-clave-ficticia", stored_hash)


def test_password_hash_uses_a_new_salt_each_time() -> None:
    password = "otra-clave-de-prueba"

    assert hash_password(password) != hash_password(password)


def test_invalid_stored_hash_is_rejected() -> None:
    assert not verify_password("clave-ficticia", "hash-danado")
