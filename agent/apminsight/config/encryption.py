import os
import re
import base64
import binascii
import subprocess


def generate_key_and_iv():
    # Generate a random 256-bit key (32 bytes) and 128-bit IV (16 bytes)
    key = os.urandom(32)  # 32 bytes for AES-256
    iv = os.urandom(16)  # 16 bytes for AES block size
    return binascii.hexlify(key).decode(), binascii.hexlify(iv).decode()


def base64_encode(text):
    if isinstance(text, str):
        text = text.encode("utf-8")
    if isinstance(text, bytes):
        return base64.b64encode(text)
    return ""


def base64_decode(text):
    if isinstance(text, str):
        text = text.encode("utf-8")
    if isinstance(text, bytes):
        return base64.b64decode(text)
    return ""


def base64_encrypt(key, iv, text):

    bytes_key = base64_decode(key)
    bytes_iv = base64_decode(iv)
    bytes_text = base64_decode(text)

    return encrypt(bytes_key, bytes_iv, bytes_text)


def encoded_string(key: bytes, ciphertext: str, iv: bytes) -> None:
    if ciphertext:
        return "-".join((base64.b64encode(key).decode("utf-8"), ciphertext, base64.b64encode(iv).decode("utf-8")))


def encoded_bytes_array(key: str, ciphertext: str, iv: str):
    return [base64.b64decode(key.encode("utf-8")), ciphertext, base64.b64decode(iv.encode("utf-8"))]


def openssl_encrypt(key: bytes, text: str, iv: bytes):
    try:
        command = ['openssl', 'enc',
                   '-aes-256-cbc',
                   '-K', key.hex()[:64],
                   '-iv', iv.hex()[:32],
                   '-base64'
                   ]

        result = subprocess.run(command, input=text, text=True,  capture_output=True, timeout=5.0, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        print("[Warning] openssl encryption failed: %s", str(exc))
    except Exception as exc:
        print("[Warning] openssl encryption failed: %s", str(exc))
    return None


def encrypt(key: bytes, text: str, iv: bytes):

    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.backends import default_backend

        # Create the cipher object
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Pad the plaintext to be a multiple of the block size (16 bytes)
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_plaintext = padder.update(text.encode("utf-8")) + padder.finalize()

        # Encrypt the padded plaintext
        ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
        return encoded_string(key, base64.b64encode(ciphertext).decode("utf-8"), iv)
    except ImportError:
        ciphertext = openssl_encrypt(key, text, iv)
        return encoded_string(key, ciphertext, iv)
    except Exception as exc:
        print("[Warning] Encryption failed: %s", str(exc))
        return None


def openssl_decrypt(key: str, ciphertext: str, iv: str):
    try:
        command = [
            "openssl",
            "enc",
            "-nopad",
            "-d",
            "-aes-256-cbc",
            "-K",
            key.hex()[:64],
            "-iv",
            iv.hex()[:32],
            "-base64",
        ]
        result = subprocess.run(
            command, input=ciphertext.encode("utf-8") + b"\n", capture_output=True, timeout=5.0, check=True
        )
        value = result.stdout.strip()

        result = value.decode("utf-8") if isinstance(result.stdout.strip(), bytes) else value
        result = re.sub(r"[\x00-\x1F\x7F]", "", result)
        return result
    except subprocess.CalledProcessError as exc:
        print("[Warning] Decryption failed: %s", str(exc))
    except Exception as exc:
        print("[Warning] Decryption failed: %s", str(exc))
    return None


def decrypt(key: bytes, ciphertext: str, iv: bytes):

    bytes_ciphertext = base64.b64decode(ciphertext.encode("utf-8"))

    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.backends import default_backend

        # Create the cipher object
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        # Decrypt the ciphertext
        padded_plaintext = decryptor.update(bytes_ciphertext) + decryptor.finalize()

        # Unpad the plaintext
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        return (unpadder.update(padded_plaintext) + unpadder.finalize()).decode("utf-8")
    except ImportError:
        return openssl_decrypt(key, ciphertext, iv)
    except Exception as exc:
        print("[Warning] Decryption failed: %s", str(exc))
        return None
