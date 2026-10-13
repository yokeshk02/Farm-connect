import secrets
from datetime import datetime, timedelta
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models.otp import OTPVerification
from app.utils.security import normalize_phone_number


class BaseSMSProvider:
    """Abstract SMS Gateway Provider Interface."""

    def send_otp(self, phone: str, otp_code: str) -> bool:
        raise NotImplementedError("SMS provider must implement send_otp()")


class MockDevSMSProvider(BaseSMSProvider):
    """Development-only mock SMS provider that logs OTP to the server terminal."""

    def send_otp(self, phone: str, otp_code: str) -> bool:
        app_env = current_app.config.get("APP_ENV", "production").lower()
        mock_enabled = current_app.config.get("MOCK_OTP_ENABLED", False)

        if app_env == "production":
            raise RuntimeError("CRITICAL SECURITY ERROR: Mock SMS provider cannot be used in production!")

        # Log OTP to the terminal strictly in local development mode
        if app_env == "development" and mock_enabled:
            print(
                f"\n{'='*60}\n"
                f"[FARMCONNECT DEV OTP]\n"
                f"Phone: {phone}\n"
                f"OTP Code: {otp_code}\n"
                f"Valid For: 5 Minutes (Max 3 attempts)\n"
                f"{'='*60}\n",
                flush=True,
            )
            return True

        # In testing mode or other non-dev environments, do not log OTP
        return True


class OTPService:
    """Cryptographic OTP lifecycle management, verification, and rate limiting."""

    COOLDOWN_SECONDS = 60
    HOURLY_LIMIT = 5
    EXPIRY_MINUTES = 5
    MAX_ATTEMPTS = 3

    def __init__(self, sms_provider: BaseSMSProvider | None = None):
        self.sms_provider = sms_provider or MockDevSMSProvider()

    def generate_otp_code(self) -> str:
        """Generate a cryptographically secure 6-digit numeric token."""
        return f"{secrets.randbelow(1_000_000):06d}"

    def request_otp(self, phone: str, purpose: str = "LOGIN") -> tuple[bool, str]:
        """Validate cooldown and limits, generate hashed OTP, and dispatch via provider."""
        try:
            normalized_phone = normalize_phone_number(phone)
        except ValueError as e:
            return False, str(e)

        now = datetime.utcnow()

        # 1. Check 60-second cooldown on most recent request
        latest_record = (
            OTPVerification.query.filter_by(phone=normalized_phone)
            .order_by(OTPVerification.created_at.desc())
            .first()
        )
        if latest_record and not latest_record.is_consumed():
            elapsed = (now - latest_record.created_at).total_seconds()
            if elapsed < self.COOLDOWN_SECONDS:
                remaining_wait = int(self.COOLDOWN_SECONDS - elapsed)
                return False, f"Please wait {remaining_wait} second(s) before requesting a new OTP."

        # 2. Check 5 requests per hour rate limit
        one_hour_ago = now - timedelta(hours=1)
        hourly_count = OTPVerification.query.filter(
            OTPVerification.phone == normalized_phone,
            OTPVerification.created_at >= one_hour_ago,
        ).count()
        if hourly_count >= self.HOURLY_LIMIT:
            return False, "Maximum OTP requests exceeded. Please try again after an hour."

        # 3. Generate secure code and store salted hash
        raw_otp = self.generate_otp_code()
        hashed_otp = generate_password_hash(raw_otp)
        expires_at = now + timedelta(minutes=self.EXPIRY_MINUTES)

        otp_record = OTPVerification(
            phone=normalized_phone,
            otp_hash=hashed_otp,
            purpose=purpose,
            attempts=0,
            max_attempts=self.MAX_ATTEMPTS,
            expires_at=expires_at,
            created_at=now,
        )
        db.session.add(otp_record)
        db.session.commit()

        # 4. Dispatch via SMS provider
        try:
            self.sms_provider.send_otp(normalized_phone, raw_otp)
        except Exception as e:
            current_app.logger.error(f"Failed to dispatch SMS: {e}")
            return False, "Failed to send verification SMS. Please try again."

        return True, "A 6-digit verification code has been sent to your mobile phone."

    def verify_otp(self, phone: str, otp_code: str, purpose: str | None = None) -> tuple[bool, str]:
        """Validate the submitted code against the hashed record, enforcing expiry and attempt limits."""
        try:
            normalized_phone = normalize_phone_number(phone)
        except ValueError as e:
            return False, str(e)

        cleaned_code = str(otp_code or "").strip()
        if not cleaned_code or len(cleaned_code) != 6 or not cleaned_code.isdigit():
            return False, "Please enter a valid 6-digit OTP code."

        query = OTPVerification.query.filter(
            OTPVerification.phone == normalized_phone,
            OTPVerification.consumed_at.is_(None),
        )
        if purpose:
            query = query.filter_by(purpose=purpose)

        record = query.order_by(OTPVerification.created_at.desc()).first()

        if not record:
            return False, "No active verification code found. Please request a new code."

        now = datetime.utcnow()
        if now > record.expires_at:
            return False, "This OTP has expired. Please request a new code."

        if record.attempts >= record.max_attempts:
            return False, "Maximum verification attempts exceeded. This OTP is now invalid. Please request a new code."

        # Verify hash
        if check_password_hash(record.otp_hash, cleaned_code):
            record.consumed_at = now
            db.session.commit()
            return True, "Phone verification successful."
        else:
            record.attempts += 1
            db.session.commit()
            remaining = record.max_attempts - record.attempts
            if remaining <= 0:
                return False, "Invalid OTP code. Maximum attempts exceeded. Please request a new code."
            return False, f"Invalid OTP code. {remaining} attempt(s) remaining."


# Global singleton instance for application use
otp_service = OTPService()
