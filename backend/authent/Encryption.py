from cryptography.fernet import Fernet
from config import settings

# Encode the key
fernet = Fernet(settings.ENCRYPTION_KEY.encode())

# Encrypt token
def encrypt_token(token: str) -> bytes:
    return fernet.encrypt(token.encode())

# Decrypt token
def decrypt_token(encrypted_token: bytes) -> str:
    return fernet.decrypt(encrypted_token).decode()

