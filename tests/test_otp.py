import re
from datetime import datetime, timedelta
import pytest
from werkzeug.security import check_password_hash
from app.services.otp_service import OTPService, MockDevSMSProvider
from app.models.otp import OTPVerification
from app.extensions import db


class CaptureSMSProvider(MockDevSMSProvider):
    """Test helper provider capturing the generated raw OTP for verification assertions."""
    def __init__(self):
        self.last_sent_code = None
        self.last_sent_phone = None

    def send_otp(self, phone: str, otp_code: str) -> bool:
        self.last_sent_phone = phone
        self.last_sent_code = otp_code
        return super().send_otp(phone, otp_code)


@pytest.fixture
def capture_otp_service():
    provider = CaptureSMSProvider()
    return OTPService(sms_provider=provider), provider


def test_otp_generation_format():
    """Verify generated OTP is a 6-digit numeric string."""
    service = OTPService()
    code = service.generate_otp_code()
    assert len(code) == 6
    assert code.isdigit()
    assert re.match(r"^\d{6}$", code)


def test_request_otp_stores_hashed_record(app, db_session, capture_otp_service):
    """Verify request_otp stores a salted hash in the database, with 5-minute expiry."""
    service, provider = capture_otp_service
    phone = "+919876500001"

    success, msg = service.request_otp(phone, purpose="LOGIN")
    assert success is True
    # The return message must never expose the raw OTP
    assert provider.last_sent_code not in msg

    record = (
        OTPVerification.query.filter_by(phone=phone)
        .order_by(OTPVerification.created_at.desc())
        .first()
    )
    assert record is not None
    assert record.otp_hash != provider.last_sent_code
    assert check_password_hash(record.otp_hash, provider.last_sent_code) is True
    assert record.attempts == 0
    assert record.consumed_at is None
    # Expiry is roughly 5 minutes from now
    diff = (record.expires_at - record.created_at).total_seconds()
    assert 290 <= diff <= 310


def test_otp_cooldown_enforcement(app, db_session, capture_otp_service):
    """Verify requesting OTP within 60 seconds is rejected with a cooldown message."""
    service, _ = capture_otp_service
    phone = "+919876500002"

    success1, _ = service.request_otp(phone)
    assert success1 is True

    # Immediate second request should fail cooldown
    success2, msg2 = service.request_otp(phone)
    assert success2 is False
    assert "Please wait" in msg2


def test_otp_hourly_rate_limit(app, db_session, capture_otp_service):
    """Verify exceeding 5 requests in an hour is rejected."""
    service, _ = capture_otp_service
    phone = "+919876500003"
    now = datetime.utcnow()

    # Pre-populate 5 records created 20 minutes ago
    for i in range(5):
        rec = OTPVerification(
            phone=phone,
            otp_hash="dummy_hash",
            purpose="LOGIN",
            expires_at=now + timedelta(minutes=5),
            created_at=now - timedelta(minutes=20 + i),
            consumed_at=now,
        )
        db_session.add(rec)
    db_session.commit()

    # 6th request within the hour must be blocked
    success, msg = service.request_otp(phone)
    assert success is False
    assert "Maximum OTP requests exceeded" in msg


def test_verify_otp_success_marks_consumed(app, db_session, capture_otp_service):
    """Verify correct OTP validates successfully and marks consumed_at."""
    service, provider = capture_otp_service
    phone = "+919876500004"

    service.request_otp(phone)
    code = provider.last_sent_code

    success, msg = service.verify_otp(phone, code)
    assert success is True

    record = OTPVerification.query.filter_by(phone=phone).first()
    assert record.consumed_at is not None

    # Cannot reuse the same consumed OTP
    success_reuse, _ = service.verify_otp(phone, code)
    assert success_reuse is False


def test_verify_otp_incorrect_code_and_lockout(app, db_session, capture_otp_service):
    """Verify incorrect OTP increments attempts and locks after 3 tries."""
    service, _ = capture_otp_service
    phone = "+919876500005"

    service.request_otp(phone)

    # Attempt 1: Wrong
    s1, msg1 = service.verify_otp(phone, "000000")
    assert s1 is False
    assert "2 attempt(s) remaining" in msg1

    # Attempt 2: Wrong
    s2, msg2 = service.verify_otp(phone, "111111")
    assert s2 is False
    assert "1 attempt(s) remaining" in msg2

    # Attempt 3: Wrong -> Maximum attempts exceeded
    s3, msg3 = service.verify_otp(phone, "222222")
    assert s3 is False
    assert "Maximum attempts exceeded" in msg3

    # Attempt 4: Even if correct code entered now, it is locked
    record = OTPVerification.query.filter_by(phone=phone).first()
    assert record.is_locked() is True


def test_verify_otp_expired_fails(app, db_session, capture_otp_service):
    """Verify expired OTP fails validation."""
    service, provider = capture_otp_service
    phone = "+919876500006"

    service.request_otp(phone)
    code = provider.last_sent_code

    # Force expiration in DB
    record = OTPVerification.query.filter_by(phone=phone).first()
    record.expires_at = datetime.utcnow() - timedelta(seconds=10)
    db_session.commit()

    success, msg = service.verify_otp(phone, code)
    assert success is False
    assert "expired" in msg.lower()


def test_mock_otp_production_rejection(app, monkeypatch):
    """Verify mock SMS provider raises RuntimeError when APP_ENV is production."""
    provider = MockDevSMSProvider()
    with app.app_context():
        monkeypatch.setitem(app.config, "APP_ENV", "production")
        with pytest.raises(RuntimeError, match="Mock SMS provider cannot be used in production"):
            provider.send_otp("+919876500007", "123456")


def test_mock_otp_does_not_log_in_testing(app, capsys):
    """Verify mock provider does NOT log OTP to console in testing environment."""
    provider = MockDevSMSProvider()
    with app.app_context():
        assert app.config["APP_ENV"] == "testing"
        provider.send_otp("+919876500008", "999888")
        captured = capsys.readouterr()
        assert "999888" not in captured.out


def test_mock_otp_logs_in_development(app, monkeypatch, capsys):
    """Verify mock provider logs [DEV MOCK SMS] to console when APP_ENV is development and MOCK_OTP_ENABLED is True."""
    provider = MockDevSMSProvider()
    with app.app_context():
        monkeypatch.setitem(app.config, "APP_ENV", "development")
        monkeypatch.setitem(app.config, "MOCK_OTP_ENABLED", True)
        provider.send_otp("+919876500009", "123789")
        captured = capsys.readouterr()
        assert "[DEV MOCK SMS]" in captured.out
        assert "123789" in captured.out
