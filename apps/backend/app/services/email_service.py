import smtplib
from email.message import current_app

class EmailService:
    @staticmethod
    def build_activation_link(raw_token):
        frontend_url = current_app.config["FRONTEND_URL"]
        return f"{frontend_url}/activate?token={raw_token}"
    
    @staticmethod
    def build_reset_link(raw_token):
        frontend_url = current_app.config["FRONTEND_URL"]
        return f"{frontend_url}/activate?token={raw_token}"
    
    @staticmethod
    def send_email(to_email, subject, body):
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = current_app.config["MAIL_DEFUALT_SENDER"]
        msg["To"] = to_email
        msg.set_content(body)

        with smtplib.SMTP(
            current_app.config["MAIL_SERVER"],
            current_app.config["MAIL_PORT"],
        ) as smtp:
            smtp.send_message(msg)

    @classmethod
    def send_activation_email(cls, user_email, raw_token):
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
        def send_password_reset_email(cls, user_email, raw_token):
            reset_link = cls.build_reset_link(raw_token)
            subject = "Reset your CADRI password"
            body = (
                "A password reset request was received for your CADRI account.\n\n"
                "You can reset your password using the following link:\n"
                f"{reset_link}\n\n"
                "This link expires in 2 hours"
            )
            cls.send_email(user_email, subject, body)