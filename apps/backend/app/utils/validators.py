import re

from app.utils.exceptions import ValidationError


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(email):
    if not email or not isinstance(email, str):
        raise ValidationError("Email is required.")

    normalized_email = email.strip().lower()

    if not EMAIL_REGEX.match(normalized_email):
        raise ValidationError("Invalid email format.")

    return normalized_email


def validate_password(password):
    if not password or not isinstance(password, str):
        raise ValidationError("Password is required.")

    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")

    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter.")

    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter.")

    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one number.")

    return password
