"""
Firebase Authentication Module for AeroPath AI
Handles Firebase Admin SDK initialization and token verification.
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, auth
from dotenv import load_dotenv
from functools import wraps
from flask import request, jsonify

load_dotenv()

# ── Initialize Firebase Admin SDK ──────────────────────────────────────────
_firebase_app = None

def _init_firebase():
    """Initialize Firebase Admin SDK (once)."""
    global _firebase_app
    if _firebase_app:
        return _firebase_app

    service_account_path = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_PATH",
        "firebase-service-account.json"
    )

    if os.path.exists(service_account_path):
        cred = credentials.Certificate(service_account_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        print(f"✅ Firebase Admin SDK initialized from {service_account_path}")
    else:
        print(f"⚠️  Firebase service account file not found at: {service_account_path}")
        print("   Server-side token verification will be disabled.")
        print("   Download it from Firebase Console → Project Settings → Service Accounts")

    return _firebase_app


# Initialize on module import
_init_firebase()


# ── Token Verification ─────────────────────────────────────────────────────

def verify_firebase_token(id_token):
    """
    Verify a Firebase ID token and return the decoded user info.
    Returns: dict with uid, email, etc. on success
    Raises: ValueError on invalid/expired token
    """
    if not _firebase_app:
        raise ValueError("Firebase Admin SDK not initialized. Missing service account file.")

    try:
        decoded = auth.verify_id_token(id_token)
        return {
            "uid": decoded["uid"],
            "email": decoded.get("email", ""),
            "email_verified": decoded.get("email_verified", False),
            "name": decoded.get("name", ""),
        }
    except auth.ExpiredIdTokenError:
        raise ValueError("Token has expired. Please sign in again.")
    except auth.InvalidIdTokenError:
        raise ValueError("Invalid authentication token.")
    except Exception as e:
        raise ValueError(f"Token verification failed: {str(e)}")


def get_user_by_email(email):
    """Look up a Firebase user by email address."""
    if not _firebase_app:
        return None
    try:
        user = auth.get_user_by_email(email)
        return {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "disabled": user.disabled,
        }
    except auth.UserNotFoundError:
        return None
    except Exception:
        return None


def set_user_role(uid, role):
    """Set custom claims (role) on a Firebase user."""
    if not _firebase_app:
        return False
    try:
        auth.set_custom_user_claims(uid, {"role": role})
        return True
    except Exception:
        return False


# ── Flask Decorator ────────────────────────────────────────────────────────

def require_auth(f):
    """
    Flask route decorator that requires a valid Firebase ID token
    in the Authorization header: 'Bearer <token>'
    Sets request.user with decoded token info on success.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split("Bearer ")[1]

        try:
            user_info = verify_firebase_token(token)
            request.user = user_info
        except ValueError as e:
            return jsonify({"error": str(e)}), 401

        return f(*args, **kwargs)

    return decorated
