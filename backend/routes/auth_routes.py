import re
import random
import datetime
from datetime import timezone, timedelta
from flask import Blueprint, request, jsonify
from backend.database.db import db
from backend.models.models import User, EmergencyContact, TrustedContact
from backend.utils.auth_helper import hash_password, check_password, generate_token, token_required

auth_bp = Blueprint('auth', __name__)

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
PHONE_REGEX = r'^\+?[1-9]\d{7,14}$'

def validate_password_complexity(password: str):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r'[0-9]', password):
        return "Password must contain at least one number."
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        return "Password must contain at least one special character (!@#$%^&*)."
    return None

def clean_phone_number(phone: str) -> str:
    if not phone:
        return ""
    phone = phone.strip()
    digits = re.sub(r'\D', '', phone)
    if not digits:
        return ""
    if len(digits) == 10:
        return f"+91{digits}"
    if not phone.startswith('+'):
        return f"+{digits}"
    return phone

def generate_otp_code() -> str:
    return str(random.randint(100000, 999999))

# -----------------------------------------------------------------------------
# 1. REGISTER (Short Registration, sends verification OTP)
# -----------------------------------------------------------------------------
@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = clean_phone_number(data.get('phone', ''))
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', data.get('password', ''))
    terms_accepted = data.get('terms_accepted', True)

    if not full_name:
        return jsonify({'error': 'Full name is required.'}), 400
    if not email or not re.match(EMAIL_REGEX, email):
        return jsonify({'error': 'Please enter a valid email address (e.g. user@gmail.com).'}), 400
    if phone and not re.match(PHONE_REGEX, phone):
        return jsonify({'error': 'Please enter a valid mobile number with country code.'}), 400
    if not terms_accepted:
        return jsonify({'error': 'You must accept the Terms & Privacy Policy to register.'}), 400

    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match.'}), 400

    pwd_err = validate_password_complexity(password)
    if pwd_err:
        return jsonify({'error': pwd_err}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'An account with this email address already exists.'}), 409

    if phone and User.query.filter(User.phone == phone).first():
        return jsonify({'error': 'An account with this mobile number already exists.'}), 409

    otp = generate_otp_code()
    now = datetime.datetime.now(timezone.utc)
    otp_expires = now + timedelta(minutes=10)

    user = User(
        full_name=full_name,
        email=email,
        phone=phone or None,
        password_hash=hash_password(password),
        is_verified=False,
        is_active=True,
        onboarding_completed=False,
        verification_otp=otp,
        verification_otp_expires_at=otp_expires,
        verification_attempts=0
    )
    db.session.add(user)
    db.session.commit()

    print(f"[AUTH VERIFICATION OTP] Sent OTP {otp} to email {email} (expires in 10 mins)")

    return jsonify({
        'message': 'Registration successful. Please verify your account using the OTP code.',
        'email': email,
        'requires_verification': True,
        'dev_otp': otp  # Exposed for frictionless automated testing & demo
    }), 201

# -----------------------------------------------------------------------------
# 2. VERIFY OTP
# -----------------------------------------------------------------------------
@auth_bp.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json() or {}
    identifier = data.get('identifier', data.get('email', '')).strip().lower()
    otp = data.get('otp', '').strip()

    if not identifier or not otp:
        return jsonify({'error': 'Email/Phone and OTP code are required.'}), 400

    user = User.query.filter((User.email == identifier) | (User.phone == identifier)).first()
    if not user:
        return jsonify({'error': 'Account not found.'}), 4404 if False else 404

    if user.is_verified:
        token = generate_token(user.id, user.email)
        user_data = user.to_dict()
        user_data['emergency_contacts'] = [c.to_dict() for c in user.emergency_contacts]
        return jsonify({
            'message': 'Account is already verified.',
            'token': token,
            'user': user_data
        }), 200

    if user.verification_attempts >= 5:
        return jsonify({'error': 'Maximum verification attempts exceeded. Please request a new OTP.'}), 429

    now = datetime.datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = user.verification_otp_expires_at.replace(tzinfo=None) if user.verification_otp_expires_at else now - datetime.timedelta(seconds=1)

    if now > expires_at:
        return jsonify({'error': 'Verification OTP has expired. Please click resend to get a new code.'}), 410

    if user.verification_otp != otp:
        user.verification_attempts += 1
        db.session.commit()
        remaining = max(0, 5 - user.verification_attempts)
        return jsonify({'error': f'Invalid OTP code. {remaining} attempt(s) remaining.'}), 400

    user.is_verified = True
    user.verification_otp = None
    user.verification_otp_expires_at = None
    user.verification_attempts = 0
    db.session.commit()

    token = generate_token(user.id, user.email)
    user_data = user.to_dict()
    user_data['emergency_contacts'] = [c.to_dict() for c in user.emergency_contacts]

    return jsonify({
        'message': 'Account verified successfully!',
        'token': token,
        'user': user_data
    }), 200

# -----------------------------------------------------------------------------
# 3. RESEND OTP
# -----------------------------------------------------------------------------
@auth_bp.route('/api/auth/resend-otp', methods=['POST'])
def resend_otp():
    data = request.get_json() or {}
    identifier = data.get('identifier', data.get('email', '')).strip().lower()

    if not identifier:
        return jsonify({'error': 'Email or phone number is required.'}), 400

    user = User.query.filter((User.email == identifier) | (User.phone == identifier)).first()
    if not user:
        return jsonify({'error': 'Account not found.'}), 404

    now = datetime.datetime.now(timezone.utc).replace(tzinfo=None)

    if user.otp_resend_cooldown_until:
        cooldown = user.otp_resend_cooldown_until.replace(tzinfo=None)
        if now < cooldown:
            remaining_seconds = int((cooldown - now).total_seconds())
            return jsonify({'error': f'Please wait {remaining_seconds} seconds before requesting a new OTP.'}), 429

    otp = generate_otp_code()
    user.verification_otp = otp
    user.verification_otp_expires_at = now + timedelta(minutes=10)
    user.otp_resend_cooldown_until = now + timedelta(seconds=60)
    user.verification_attempts = 0
    db.session.commit()

    print(f"[AUTH RESEND OTP] Sent new OTP {otp} to {identifier}")

    return jsonify({
        'message': 'A new verification OTP code has been sent.',
        'dev_otp': otp
    }), 200

# -----------------------------------------------------------------------------
# 4. LOGIN
# -----------------------------------------------------------------------------
@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    identifier = data.get('identifier', data.get('email', '')).strip().lower()
    password = data.get('password', '')

    if not identifier or not password:
        return jsonify({'error': 'Please enter both your email/mobile and password.'}), 400

    user = User.query.filter((User.email == identifier) | (User.phone == identifier)).first()
    if not user or not check_password(password, user.password_hash):
        return jsonify({'error': 'Invalid email/mobile or password. Please try again.'}), 401

    if not user.is_active:
        return jsonify({'error': 'Your account has been deactivated or locked. Please contact support.'}), 403

    if not user.is_verified:
        otp = generate_otp_code()
        user.verification_otp = otp
        user.verification_otp_expires_at = datetime.datetime.now(timezone.utc) + timedelta(minutes=10)
        db.session.commit()
        return jsonify({
            'error': 'Your account is unverified. We have sent a verification code to your email.',
            'requires_verification': True,
            'email': user.email,
            'dev_otp': otp
        }), 403

    token = generate_token(user.id, user.email)
    user_data = user.to_dict()
    user_data['emergency_contacts'] = [c.to_dict() for c in user.emergency_contacts]

    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': user_data
    }), 200

# -----------------------------------------------------------------------------
# 5. FORGOT PASSWORD
# -----------------------------------------------------------------------------
@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    identifier = data.get('identifier', data.get('email', '')).strip().lower()

    if not identifier:
        return jsonify({'error': 'Please enter your email address or mobile number.'}), 400

    user = User.query.filter((User.email == identifier) | (User.phone == identifier)).first()
    if not user:
        return jsonify({'message': 'If an account matches those details, a reset OTP code has been sent.'}), 200

    otp = generate_otp_code()
    now = datetime.datetime.now(timezone.utc)
    user.reset_otp = otp
    user.reset_otp_expires_at = now + timedelta(minutes=15)
    user.reset_attempts = 0
    db.session.commit()

    print(f"[AUTH FORGOT PASSWORD] Sent reset OTP {otp} to {identifier}")

    return jsonify({
        'message': 'A password reset OTP code has been sent.',
        'dev_otp': otp
    }), 200

# -----------------------------------------------------------------------------
# 6. RESET PASSWORD
# -----------------------------------------------------------------------------
@auth_bp.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json() or {}
    identifier = data.get('identifier', data.get('email', '')).strip().lower()
    otp = data.get('otp', '').strip()
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', new_password)

    if not identifier or not otp or not new_password:
        return jsonify({'error': 'Email/Phone, OTP code, and new password are required.'}), 400

    if new_password != confirm_password:
        return jsonify({'error': 'New passwords do not match.'}), 400

    pwd_err = validate_password_complexity(new_password)
    if pwd_err:
        return jsonify({'error': pwd_err}), 400

    user = User.query.filter((User.email == identifier) | (User.phone == identifier)).first()
    if not user or not user.reset_otp:
        return jsonify({'error': 'Invalid reset request or OTP expired.'}), 400

    now = datetime.datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = user.reset_otp_expires_at.replace(tzinfo=None) if user.reset_otp_expires_at else None

    if not expires_at or now > expires_at:
        return jsonify({'error': 'Password reset OTP code has expired. Please request a new code.'}), 410

    if user.reset_otp != otp:
        user.reset_attempts += 1
        db.session.commit()
        return jsonify({'error': 'Invalid reset OTP code.'}), 400

    user.password_hash = hash_password(new_password)
    user.reset_otp = None
    user.reset_otp_expires_at = None
    user.reset_attempts = 0
    db.session.commit()

    return jsonify({
        'message': 'Your password has been successfully updated! You can now log in.'
    }), 200

# -----------------------------------------------------------------------------
# 7. ONBOARDING / PROFILE SETUP (Emergency Contacts & Safety Setup)
# -----------------------------------------------------------------------------
@auth_bp.route('/api/auth/profile-setup', methods=['POST'])
@token_required
def profile_setup():
    user_id = getattr(request, 'current_user_id', None)
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    data = request.get_json() or {}
    ec_name = data.get('emergency_contact_name', '').strip()
    ec_phone = clean_phone_number(data.get('emergency_contact_phone', ''))
    ec_rel = data.get('emergency_contact_rel', 'Family')

    if ec_name and ec_phone:
        contact = EmergencyContact.query.filter_by(user_id=user.id, phone=ec_phone).first()
        if not contact:
            contact = EmergencyContact(
                user_id=user.id,
                name=ec_name,
                phone=ec_phone,
                relationship=ec_rel
            )
            db.session.add(contact)
        else:
            contact.name = ec_name
            contact.relationship = ec_rel

    user.onboarding_completed = True
    db.session.commit()

    user_data = user.to_dict()
    user_data['emergency_contacts'] = [c.to_dict() for c in user.emergency_contacts]

    return jsonify({
        'message': 'Profile setup completed successfully!',
        'user': user_data
    }), 200

# -----------------------------------------------------------------------------
# 8. GET CURRENT USER PROFILE (/api/auth/me)
# -----------------------------------------------------------------------------
@auth_bp.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user():
    user_id = getattr(request, 'current_user_id', None)
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    user_data = user.to_dict()
    user_data['emergency_contacts'] = [c.to_dict() for c in user.emergency_contacts]
    user_data['trusted_contacts'] = [c.to_dict() for c in user.trusted_contacts]
    return jsonify({'user': user_data}), 200
