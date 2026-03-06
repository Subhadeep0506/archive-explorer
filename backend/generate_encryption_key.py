"""
Generate a Fernet encryption key for API key encryption.
Run this once to generate a key, then add it to your .env file.
"""

from cryptography.fernet import Fernet

# Generate a new Fernet key
key = Fernet.generate_key()
print("=" * 60)
print("ENCRYPTION KEY GENERATED")
print("=" * 60)
print("\nAdd this line to your .env file:")
print(f"\nENCRYPTION_KEY={key.decode()}")
print("\n" + "=" * 60)
print("⚠️  IMPORTANT: Keep this key secure and never commit it to git!")
print("=" * 60)
