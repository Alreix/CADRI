"""Email delivery helpers for CADRI notification workflows.

This service builds activation and password reset links, then sends the
corresponding email messages using the application's mail settings.
"""

import smtplib
from email.message import EmailMessage

from flask import current_app

class EmailService:
    """Utilities for building and sending email notifications.

    All methods are implemented as stateless helpers. Email content is kept
    simple and plain-text; the frontend URL is read from configuration so the
    same code works across environments.
    """
    @staticmethod
    def build_activation_link(raw_token: str) -> str:
        """Build the frontend activation URL for a raw token."""

        frontend_url = current_app.config["FRONTEND_URL"]
        return f"{frontend_url}/activate?token={raw_token}"
    
    @staticmethod
    def build_reset_link(raw_token: str) -> str:
        """Build the frontend password-reset URL for a raw token."""

        frontend_url = current_app.config["FRONTEND_URL"]
        return f"{frontend_url}/reset-password?token={raw_token}"
    
    @staticmethod
    def send_email(to_email: str, subject: str, body: str) -> None:
        """Send a plain-text email using the configured SMTP server."""

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
        msg["To"] = to_email
        msg.set_content(body)

        with smtplib.SMTP(
            current_app.config["MAIL_SERVER"],
            current_app.config["MAIL_PORT"],
        ) as smtp:
            smtp.send_message(msg)

    @classmethod
    def send_activation_email(cls, user_email: str, raw_token: str) -> None:
        """Send the account activation email to a new CADRI user."""

        activation_link = cls.build_activation_link(raw_token)
        subject = "Activate your CADRI account"
        body = (
            "Welcome to CADRI.\n\n"
            "Please activate your account using the following link:\n"
            f"{activation_link}\n\n"
            "This link expires in 24 hours."
        )
        cls.send_email(user_email, subject, body)

    @classmethod
    def send_password_reset_email(cls, user_email: str, raw_token: str) -> None:
        """Send the password reset email to an existing CADRI user."""

        reset_link = cls.build_reset_link(raw_token)
        subject = "Reset your CADRI password"
        body = (
            "A password reset request was received for your CADRI account.\n\n"
            "You can reset your password using the following link:\n"
            f"{reset_link}\n\n"
            "This link expires in 2 hours."
        )
        cls.send_email(user_email, subject, body)
