"""
Resonance Club Platform — FastAPI + SQLAdmin Application (v1.0.2)
Automatically generates full CRUD tables and forms from SQLAlchemy models.
"""

import os
import sys
import argparse
import hmac
import hashlib
import base64
import json
import time
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin
from sqladmin.forms import ModelConverter, converts

# Register Float converter for SQLAdmin auto-generated forms
ModelConverter.conv_decimal = converts("Numeric", "Float")(ModelConverter.conv_decimal)

from database import async_engine, init_db
from seed_db import seed_database
from admin_views import (
    UserAdmin,
    ProfileAdmin,
    VoiceBioAdmin,
    WeeklyMatchAdmin,
    VenueAdmin,
    DateBookingAdmin,
    QuestionAdmin,
    SubscriptionAdmin
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database is initialized and seeded on startup
    init_db()
    seed_database()
    yield


app = FastAPI(
    title="Клуб «РЕЗОНАНС» — FastAPI + SQLAdmin",
    description="The Anti-Swipe Society Platform with SQLAdmin Framework for SQLAlchemy",
    version="1.0.2",
    lifespan=lifespan
)

# Mount static CSS / assets
static_dir = os.path.join(BASE_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Serve landing page, profile, and media files
@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


# ----------------------------------------------------------------------
# AUTHENTICATION API FOR RESIDENTS (ALL ROLES EXCEPT SUPERADMIN)
# ----------------------------------------------------------------------
from pydantic import BaseModel
from database import SyncSessionLocal
from models import User, Profile

AUTH_SECRET_KEY = "resonance_auth_secret_token_vault_key_2026"


def create_access_token(user_id: int, email: str, role: str, expires_in: int = 86400 * 7) -> str:
    """Creates a cryptographically signed HMAC-SHA256 bearer session token."""
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": int(time.time()) + expires_in,
        "iat": int(time.time()),
    }
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hmac.new(AUTH_SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_access_token(token: str) -> dict | None:
    """Verifies HMAC signature, integrity, and expiration of the bearer token."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig = parts
        expected_sig = hmac.new(AUTH_SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        rem = len(payload_b64) % 4
        if rem > 0:
            payload_b64 += "=" * (4 - rem)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def serialize_user(user: User) -> dict:
    profile_data = {}
    if user.profile:
        profile_data = {
            "age": user.profile.age,
            "city": user.profile.city,
            "occupation": user.profile.occupation,
            "archetype": user.profile.archetype,
            "bio": user.profile.bio,
            "acoustic_frequency_hz": user.profile.acoustic_frequency_hz,
            "photos_unlocked": user.profile.photos_unlocked
        }

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "gender": user.gender,
        "role": user.role,
        "status": user.status,
        "vip_pass_code": user.vip_pass_code,
        "reputation_score": user.reputation_score,
        "profile": profile_data
    }


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/auth/login")
def auth_login(req: LoginRequest, response: Response):
    """
    Step 5-8: Authenticate user by email & password.
    - Checks user existence in Database
    - Verifies PBKDF2 password hash
    - Restricts Superadmin to /admin
    - Issues signed bearer session token and sets secure session cookie
    """
    email = req.email.strip().lower()
    password = req.password.strip()

    if not email or not password:
        response.status_code = 400
        return {
            "success": False,
            "error": "empty_fields",
            "message": "Пожалуйста, укажите email и пароль."
        }

    session = SyncSessionLocal()
    try:
        # Step 6: Backend checks presence of user in database by email
        user = session.query(User).filter(User.email.ilike(email)).first()
        if not user:
            response.status_code = 404
            return {
                "success": False,
                "error": "user_not_found",
                "message": "Пользователь с указанным email не зарегистрирован в клубе."
            }

        # Step 7: Backend checks password correctness
        if not user.check_password(password):
            response.status_code = 401
            return {
                "success": False,
                "error": "invalid_password",
                "message": "Неверный пароль. Пожалуйста, проверьте правильность ввода."
            }

        # Restriction: Superadmin cannot log in through the public landing page form
        if user.role == "superadmin":
            response.status_code = 403
            return {
                "success": False,
                "error": "superadmin_restricted",
                "message": "Доступ для роли Superadmin осуществляется исключительно через защищенную панель /admin",
                "admin_url": "/admin"
            }

        # Step 8: Server creates session and issues authorization token
        token = create_access_token(user.id, user.email, user.role)
        response.set_cookie(
            key="resonance_session",
            value=token,
            httponly=True,
            samesite="lax",
            max_age=86400 * 7
        )

        user_data = serialize_user(user)

        # Step 9: Returns token and authorized user data
        return {
            "success": True,
            "token_type": "Bearer",
            "access_token": token,
            "expires_in": 86400 * 7,
            "user": user_data
        }
    finally:
        session.close()


@app.get("/api/auth/me")
def auth_me(request: Request, response: Response):
    """
    Verifies the user's active session token against the database
    via Authorization Bearer header or resonance_session cookie.
    """
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    elif "resonance_session" in request.cookies:
        token = request.cookies.get("resonance_session")

    if not token:
        response.status_code = 401
        return {"authenticated": False, "message": "Токен авторизации отсутствует"}

    payload = verify_access_token(token)
    if not payload:
        response.status_code = 401
        return {"authenticated": False, "message": "Токен авторизации недействителен или истек"}

    session = SyncSessionLocal()
    try:
        user = session.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            response.status_code = 404
            return {"authenticated": False, "message": "Пользователь не найден в базе данных"}

        return {
            "authenticated": True,
            "user": serialize_user(user)
        }
    finally:
        session.close()


@app.post("/api/auth/logout")
def auth_logout(response: Response):
    """Clears the session cookie on backend."""
    response.delete_cookie("resonance_session")
    return {"success": True, "message": "Сессия успешно завершена"}


@app.get("/api/auth/residents")
def get_demo_residents():
    session = SyncSessionLocal()
    try:
        # All roles EXCEPT superadmin
        residents = (
            session.query(User)
            .filter(User.role != "superadmin")
            .order_by(User.id.asc())
            .all()
        )
        result = []
        for u in residents:
            p = u.profile
            result.append({
                "id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "password": u.plain_password or "Resonance2026!",
                "role": u.role,
                "status": u.status,
                "vip_pass_code": u.vip_pass_code,
                "gender": u.gender,
                "age": p.age if p else 28,
                "city": p.city if p else "Москва",
                "occupation": p.occupation if p else "Резидент клуба",
                "archetype": p.archetype if p else "Искатель"
            })
        return result
    finally:
        session.close()


@app.api_route("/index.html", methods=["GET", "HEAD"])
async def index_page():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


@app.api_route("/profile.html", methods=["GET", "HEAD"])
async def profile_page():
    return FileResponse(os.path.join(BASE_DIR, "profile.html"))


@app.api_route("/admin.htm", methods=["GET", "HEAD"])
async def admin_htm_page():
    return FileResponse(os.path.join(BASE_DIR, "admin.htm"))


@app.api_route("/logo.svg", methods=["GET", "HEAD"])
async def logo_svg():
    return FileResponse(os.path.join(BASE_DIR, "logo.svg"), media_type="image/svg+xml")


@app.api_route("/brand_symbol.png", methods=["GET", "HEAD"])
async def brand_symbol():
    return FileResponse(os.path.join(BASE_DIR, "brand_symbol.png"), media_type="image/png")


@app.api_route("/questions_100.json", methods=["GET", "HEAD"])
async def questions_json():
    return FileResponse(os.path.join(BASE_DIR, "questions_100.json"), media_type="application/json")


# Audio files streaming endpoints
for audio_name in [
    "alexander_voice.mp3",
    "anna_voice.mp3",
    "sofia_voice.mp3",
    "polina_voice.mp3",
    "elena_voice.mp3"
]:
    def make_audio_route(file_name):
        async def audio_route():
            return FileResponse(os.path.join(BASE_DIR, file_name), media_type="audio/mpeg")
        return audio_route

    app.add_api_route(f"/{audio_name}", make_audio_route(audio_name), methods=["GET", "HEAD"])


# Setup SQLAdmin with Custom Resonance Templates and Styling
templates_dir = os.path.join(BASE_DIR, "admin_templates")

admin = Admin(
    app=app,
    engine=async_engine,
    base_url="/admin",
    title="РЕЗОНАНС • SQLADMIN",
    logo_url="/logo.svg",
    templates_dir=templates_dir
)

# Register all ModelViews (auto-generates tables, forms, details, filters)
admin.add_model_view(UserAdmin)
admin.add_model_view(ProfileAdmin)
admin.add_model_view(VoiceBioAdmin)
admin.add_model_view(WeeklyMatchAdmin)
admin.add_model_view(VenueAdmin)
admin.add_model_view(DateBookingAdmin)
admin.add_model_view(QuestionAdmin)
admin.add_model_view(SubscriptionAdmin)


def main():
    parser = argparse.ArgumentParser(description="Run Resonance Platform and SQLAdmin")
    parser.add_argument("--host", default="0.0.0.0", help="Host address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=3000, help="Port to listen on (default: 3000)")
    args = parser.parse_args()

    print("=" * 70)
    print("  RESONANCE CLUB — FASTAPI + SQLADMIN BACKEND (v1.0.2)")
    print("=" * 70)
    print(f"  🌐 Витрина Клуба (Лендинг): http://localhost:{args.port}/")
    print(f"  💎 SQLAdmin Панель Консьержа: http://localhost:{args.port}/admin")
    print(f"  👤 Кабинет Резидента: http://localhost:{args.port}/profile.html")
    print("=" * 70)

    try:
        uvicorn.run("app_admin:app", host=args.host, port=args.port, reload=False)
    except OSError as e:
        alt_port = 8000 if args.port != 8000 else 8080
        print(f"\n[WARNING] Port {args.port} is already in use or unavailable: {e}")
        print(f"[INFO] Switching to fallback port {alt_port}...")
        print(f"  🌐 Витрина Клуба: http://localhost:{alt_port}/")
        print(f"  💎 SQLAdmin Панель Консьержа: http://localhost:{alt_port}/admin\n")
        uvicorn.run("app_admin:app", host=args.host, port=alt_port, reload=False)


if __name__ == "__main__":
    main()
