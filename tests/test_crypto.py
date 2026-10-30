import pytest

from app.core.crypto import (
    decrypt_bytes,
    derive_kek,
    derive_share_key,
    encrypt_bytes,
    generate_salt,
    generate_vault_key,
    sha256_hex,
    unwrap_file_key,
    unwrap_vault_key,
    wrap_file_key,
    wrap_vault_key,
)


def test_wrap_unwrap_roundtrip():
    salt = generate_salt()
    vault_key = generate_vault_key()
    wrapped = wrap_vault_key(vault_key, "secret123", salt)
    assert wrapped != vault_key
    assert unwrap_vault_key(wrapped, "secret123", salt) == vault_key


def test_unwrap_wrong_password_raises():
    salt = generate_salt()
    wrapped = wrap_vault_key(generate_vault_key(), "secret123", salt)
    with pytest.raises(ValueError):
        unwrap_vault_key(wrapped, "wrong-password", salt)


def test_file_encrypt_decrypt_roundtrip():
    vault_key = generate_vault_key()
    file_key = generate_vault_key()
    wrapped = wrap_file_key(file_key, vault_key)
    plaintext = b"top secret vault contents"
    ciphertext = encrypt_bytes(file_key, plaintext)
    assert ciphertext != plaintext
    recovered_key = unwrap_file_key(wrapped, vault_key)
    assert decrypt_bytes(recovered_key, ciphertext) == plaintext


def test_decrypt_with_wrong_key_raises():
    ciphertext = encrypt_bytes(generate_vault_key(), b"hello")
    with pytest.raises(ValueError):
        decrypt_bytes(generate_vault_key(), ciphertext)


def test_share_key_is_deterministic():
    assert derive_share_key("abc") == derive_share_key("abc")
    assert derive_share_key("abc") != derive_share_key("abd")


def test_sha256_hex():
    assert sha256_hex(b"") == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )


def test_kek_differs_per_salt():
    assert derive_kek("secret123", b"0" * 16) != derive_kek("secret123", b"1" * 16)
