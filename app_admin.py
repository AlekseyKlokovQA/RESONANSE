"""
Resonance Club Platform — FastAPI + SQLAdmin Application (v1.0.2)
Automatically generates full CRUD tables and forms from SQLAlchemy models.
"""

import os
import sys
import argparse
import subprocess
import hmac
import hashlib
import base64
import json
import time
import uvicorn
import numpy as np
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, UploadFile, File, Form
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

# Mount uploads directory for audio voice bios & media
uploads_dir = os.path.join(BASE_DIR, "uploads")
os.makedirs(os.path.join(uploads_dir, "voice_bios"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


# Serve landing page, profile, and media files
@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


# ----------------------------------------------------------------------
# AUTHENTICATION API FOR RESIDENTS (ALL ROLES EXCEPT SUPERADMIN)
# ----------------------------------------------------------------------
from pydantic import BaseModel
from database import SyncSessionLocal
from models import User, Profile, VoiceBio, WeeklyMatch, DateBooking, Venue

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


def serialize_user(user: User, session=None) -> dict:
    """Serializes full resident profile, voice bio, and active weekly match."""
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

    voice_data = None
    if user.voice_bio:
        voice_data = {
            "id": user.voice_bio.id,
            "audio_file": user.voice_bio.audio_file,
            "duration_sec": user.voice_bio.duration_sec,
            "transcription": user.voice_bio.transcription,
            "pitch_f0": user.voice_bio.pitch_f0,
            "prompt_topic": getattr(user.voice_bio, 'prompt_topic', None),
            "spectrogram_json": getattr(user.voice_bio, 'spectrogram_json', None),
            "status": user.voice_bio.status,
            "verified_at": user.voice_bio.verified_at.isoformat() if user.voice_bio.verified_at else None
        }

    match_data = None
    if session:
        wm = (
            session.query(WeeklyMatch)
            .filter((WeeklyMatch.user1_id == user.id) | (WeeklyMatch.user2_id == user.id))
            .first()
        )
        if wm:
            p_id = wm.user2_id if wm.user1_id == user.id else wm.user1_id
            partner = session.query(User).filter(User.id == p_id).first()
            if partner:
                booking = session.query(DateBooking).filter(DateBooking.match_id == wm.id).first()
                venue_data = None
                if booking:
                    v = session.query(Venue).filter(Venue.id == booking.venue_id).first()
                    if v:
                        venue_data = {
                            "name": v.name,
                            "address": v.address,
                            "time": str(booking.booking_time)[:16],
                            "status": booking.status,
                            "perk": v.club_perk
                        }
                match_data = {
                    "match_id": wm.id,
                    "resonance_score": wm.resonance_score,
                    "status": wm.status,
                    "partner": {
                        "id": partner.id,
                        "full_name": partner.full_name,
                        "first_name": partner.full_name.split()[0],
                        "age": partner.profile.age if partner.profile else 28,
                        "occupation": partner.profile.occupation if partner.profile else "Резидент",
                        "city": partner.profile.city if partner.profile else "Москва",
                        "acoustic_frequency_hz": partner.profile.acoustic_frequency_hz if partner.profile else 432,
                        "voice_file": partner.voice_bio.audio_file if partner.voice_bio else "sofia_voice.mp3"
                    },
                    "venue": venue_data
                }

    return {
        "id": user.id,
        "full_name": user.full_name,
        "first_name": user.full_name.split()[0],
        "email": user.email,
        "phone": user.phone,
        "gender": user.gender,
        "role": user.role,
        "status": user.status,
        "vip_pass_code": user.vip_pass_code,
        "reputation_score": user.reputation_score,
        "profile": profile_data,
        "voice_bio": voice_data,
        "match": match_data
    }


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    phone: str
    gender: str
    age: int
    city: str = "Москва"
    target_gender: str = "Девушку"
    goal: str = "Для романтических отношений"
    password: str


@app.post("/api/auth/register")
def auth_register(req: RegisterRequest, response: Response):
    """
    Onboarding / Registration endpoint for new candidates:
    - Validates presence of all required fields
    - Checks for existing email in SQLite database
    - Generates unique VIP pass code
    - Creates User (status='waitlist', role='candidate') and Profile in DB
    - Issues signed bearer session token and sets session cookie
    """
    import random
    full_name = req.full_name.strip()
    email = req.email.strip().lower()
    phone = req.phone.strip()
    password = req.password.strip()

    if not full_name or not email or not phone or not password:
        response.status_code = 400
        return {
            "success": False,
            "error": "empty_fields",
            "message": "Пожалуйста, заполните все обязательные поля анкеты."
        }

    if len(password) < 6:
        response.status_code = 400
        return {
            "success": False,
            "error": "short_password",
            "message": "Пароль должен содержать не менее 6 символов."
        }

    if req.age < 18 or req.age > 120:
        response.status_code = 400
        return {
            "success": False,
            "error": "invalid_age",
            "message": "Вступление в клуб «Резонанс» доступно только совершеннолетним кандидатам (от 18 лет)."
        }

    session = SyncSessionLocal()
    try:
        # Check if email is already in database
        existing_email = session.query(User).filter(User.email.ilike(email)).first()
        if existing_email:
            response.status_code = 409
            return {
                "success": False,
                "error": "email_exists",
                "message": f"Пользователь с адресом {email} уже зарегистрирован в клубе. Пожалуйста, используйте форму входа."
            }

        # Check if phone is already registered
        if phone:
            existing_phone = session.query(User).filter(User.phone == phone).first()
            if existing_phone:
                response.status_code = 409
                return {
                    "success": False,
                    "error": "phone_exists",
                    "message": f"Пользователь с номером {phone} уже зарегистрирован в клубе. Пожалуйста, используйте форму входа."
                }

        city_map = {"msk": "Москва", "spb": "Санкт-Петербург", "other": "Другой город"}
        city = city_map.get(req.city.lower(), req.city)

        gender_map = {"male": "Мужчина", "female": "Женщина"}
        gender = gender_map.get(req.gender.lower(), req.gender)

        target_gender_map = {"woman": "Девушку", "man": "Мужчину", "any": "Не имеет значения"}
        target_gender = target_gender_map.get(req.target_gender.lower(), req.target_gender)

        goal_map = {
            "romance": "Для романтических отношений",
            "friendship": "Для дружбы и общения",
            "leisure": "Для досуга и активностей"
        }
        goal = goal_map.get(req.goal.lower(), req.goal)

        vip_code = f"RES-{random.randint(1000, 9999)}-WAIT"

        user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            gender=gender,
            target_gender=target_gender,
            goal=goal,
            status="waitlist",
            role="candidate",
            vip_pass_code=vip_code,
            reputation_score=5.0
        )
        user.set_password(password)
        session.add(user)
        session.flush()

        profile = Profile(
            user_id=user.id,
            age=req.age,
            city=city,
            occupation="Кандидат клуба",
            bio=f"Заявка в лист ожидания клуба «Резонанс». Цель: {goal}. Город: {city}.",
            archetype="Искатель • Кандидат",
            acoustic_frequency_hz=432 if gender == "Мужчина" else 528,
            photos_unlocked=False
        )
        session.add(profile)
        session.commit()

        token = create_access_token(user.id, user.email, user.role)
        response.set_cookie(
            key="resonance_session",
            value=token,
            httponly=True,
            samesite="lax",
            max_age=86400 * 7
        )

        user_data = serialize_user(user, session=session)

        return {
            "success": True,
            "message": "Заявка успешно принята в лист ожидания клуба!",
            "access_token": token,
            "user": user_data
        }
    except Exception as e:
        session.rollback()
        response.status_code = 400
        return {
            "success": False,
            "error": "registration_failed",
            "message": f"Ошибка регистрации: {str(e)}"
        }
    finally:
        session.close()


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

        user_data = serialize_user(user, session=session)

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
            "user": serialize_user(user, session=session)
        }
    finally:
        session.close()


@app.get("/api/users/{identifier}")
def get_user_profile(identifier: str):
    """Returns the full public profile and match data for a resident by ID or Email."""
    session = SyncSessionLocal()
    try:
        ident = identifier.strip()
        if ident.isdigit():
            user = session.query(User).filter(User.id == int(ident)).first()
        else:
            user = session.query(User).filter(User.email.ilike(ident)).first()

        if not user:
            return JSONResponse(status_code=404, content={"success": False, "message": "Резидент не найден"})

        if user.role == "superadmin":
            return JSONResponse(status_code=403, content={"success": False, "message": "Доступ к профилю суперадминистратора ограничен"})

        return {"success": True, "user": serialize_user(user, session=session)}
    finally:
        session.close()


@app.post("/api/auth/logout")
def auth_logout(response: Response):
    """Clears the session cookie on backend."""
    response.delete_cookie("resonance_session")
    return {"success": True, "message": "Сессия успешно завершена"}
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


def analyze_audio_file(file_path: str) -> dict:
    """
    Module 2: Analyzes audio file (webm, wav, mp3, ogg, m4a) using ffmpeg & numpy.
    - Measures duration in seconds
    - Estimates fundamental speech frequency F0 (in Hz, typically 80-320 Hz)
    - Generates 16x32 normalized frequency spectrogram matrix for client heatmap
    - Computes club harmonic resonance (432 Hz / 528 Hz) and timbre warmth
    """
    duration_sec = 24
    pitch_f0 = 136.1
    # Fallback synthetic harmonic spectrogram
    spectrogram = [[int(20 + 50 * np.sin(i * 0.4 + j * 0.2)**2) for j in range(32)] for i in range(16)]

    try:
        cmd = ['ffmpeg', '-i', file_path, '-f', 's16le', '-ac', '1', '-ar', '16000', 'pipe:1']
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        if res.returncode == 0 and len(res.stdout) > 3200:
            samples = np.frombuffer(res.stdout, dtype=np.int16).astype(np.float32)
            calc_dur = len(samples) / 16000.0
            if calc_dur > 0.3:
                duration_sec = max(1, round(calc_dur))

            # Pitch F0 estimation via autocorrelation in speech frequency band (75 - 320 Hz)
            min_lag = int(16000 / 320)
            max_lag = int(16000 / 75)
            mid = len(samples) // 2
            seg_len = min(4096, len(samples))
            seg = samples[mid - seg_len//2 : mid + seg_len//2]
            if len(seg) >= 2048:
                seg = seg - np.mean(seg)
                corr = np.correlate(seg, seg, mode='full')
                corr = corr[len(corr)//2:]
                if max_lag < len(corr):
                    peak_lag = min_lag + np.argmax(corr[min_lag:max_lag])
                    calc_f0 = 16000.0 / peak_lag
                    if 70 <= calc_f0 <= 350:
                        pitch_f0 = round(float(calc_f0), 1)

            # Spectrogram generation: 16 time frames x 32 frequency bands
            frame_size = 512
            hop_size = max(1, (len(samples) - frame_size) // 16)
            frames = []
            for i in range(16):
                start = i * hop_size
                frame = samples[start:start+frame_size]
                if len(frame) < frame_size:
                    frame = np.pad(frame, (0, frame_size - len(frame)))
                windowed = frame * np.hanning(frame_size)
                fft_mag = np.abs(np.fft.rfft(windowed))[:32]
                max_val = np.max(fft_mag)
                if max_val > 0:
                    norm = (fft_mag / max_val * 100).astype(int).tolist()
                else:
                    norm = [15] * 32
                frames.append(norm)
            spectrogram = frames
    except Exception as e:
        print(f"Warning: Audio analysis fallback used: {e}")

    # Determine harmonic club keynote & timbre classification
    if pitch_f0 < 170:
        club_freq = 432
        timbre_label = "Глубокий бархатный баритон / темный тембр"
        harmonic_interval = "Чистая квинта (земное гармоническое основание)"
    else:
        club_freq = 528
        timbre_label = "Светлое сопрано / ясный мелодичный обертон"
        harmonic_interval = "Мажорная секста (частота трансформации и созвучия)"

    return {
        "duration_sec": duration_sec,
        "pitch_f0": pitch_f0,
        "resonance_frequency_hz": club_freq,
        "timbre_warmth": timbre_label,
        "harmonic_interval": harmonic_interval,
        "spectrogram": spectrogram
    }


@app.post("/api/voice/upload")
async def upload_voice_bio(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    topic: str = Form("О чем я могу говорить часами без остановки"),
    user_id: int = Form(None),
    transcription: str = Form(None)
):
    """
    Module 2: Audio Voice Bio Recording & Spectrogram Analysis.
    - Validates audio format (webm, wav, mp3, ogg, m4a, etc.)
    - Resolves user via Bearer token, session cookie, or form user_id
    - Saves audio to /uploads/voice_bios/
    - Computes pitch F0, duration, and 16x32 frequency spectrogram
    - Updates/creates VoiceBio and updates Profile.acoustic_frequency_hz
    - Returns serialized voice bio and acoustic metrics
    """
    target_user_id = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        payload = verify_access_token(auth_header.split(" ")[1])
        if payload:
            target_user_id = payload.get("sub")
    elif "resonance_session" in request.cookies:
        payload = verify_access_token(request.cookies.get("resonance_session"))
        if payload:
            target_user_id = payload.get("sub")

    if not target_user_id and user_id:
        target_user_id = user_id

    if not target_user_id:
        response.status_code = 401
        return {
            "success": False,
            "error": "unauthorized",
            "message": "Для сохранения голосовой визитки требуется авторизация в клубе."
        }

    # Determine file extension
    original_name = file.filename or "recording.webm"
    ext = os.path.splitext(original_name)[1].lower().lstrip(".")
    if not ext or ext not in ["webm", "wav", "mp3", "ogg", "m4a", "aac", "mp4"]:
        ext = "webm"

    filename = f"voice_u{target_user_id}_{int(time.time())}.{ext}"
    voice_dir = os.path.join(uploads_dir, "voice_bios")
    os.makedirs(voice_dir, exist_ok=True)
    saved_path = os.path.join(voice_dir, filename)

    content = await file.read()
    if not content or len(content) < 100:
        response.status_code = 400
        return {
            "success": False,
            "error": "empty_audio",
            "message": "Передан пустой или поврежденный аудиофайл."
        }

    with open(saved_path, "wb") as f:
        f.write(content)

    analysis = analyze_audio_file(saved_path)

    clean_topic = topic.strip() if topic else "О чем я могу говорить часами без остановки"
    clean_transcription = transcription.strip() if transcription else f"Запись голосовой визитки на тему: «{clean_topic}». Тон F0: {analysis['pitch_f0']} Гц."

    session = SyncSessionLocal()
    try:
        user = session.query(User).filter(User.id == target_user_id).first()
        if not user:
            response.status_code = 404
            return {"success": False, "message": "Пользователь не найден в базе данных"}

        audio_url = f"/uploads/voice_bios/{filename}"
        voice_bio = session.query(VoiceBio).filter(VoiceBio.user_id == user.id).first()

        if not voice_bio:
            voice_bio = VoiceBio(
                user_id=user.id,
                audio_file=audio_url,
                duration_sec=analysis["duration_sec"],
                pitch_f0=analysis["pitch_f0"],
                prompt_topic=clean_topic,
                transcription=clean_transcription,
                spectrogram_json=json.dumps(analysis["spectrogram"]),
                status="pending"
            )
            session.add(voice_bio)
        else:
            voice_bio.audio_file = audio_url
            voice_bio.duration_sec = analysis["duration_sec"]
            voice_bio.pitch_f0 = analysis["pitch_f0"]
            voice_bio.prompt_topic = clean_topic
            voice_bio.transcription = clean_transcription
            voice_bio.spectrogram_json = json.dumps(analysis["spectrogram"])
            voice_bio.status = "pending"

        if user.profile:
            user.profile.acoustic_frequency_hz = float(analysis["resonance_frequency_hz"])

        session.commit()

        return {
            "success": True,
            "message": "Голосовая визитка успешно сохранена и отправлена на верификацию Консьержу клуба!",
            "voice_bio": {
                "id": voice_bio.id,
                "user_id": user.id,
                "audio_file": voice_bio.audio_file,
                "duration_sec": voice_bio.duration_sec,
                "pitch_f0": voice_bio.pitch_f0,
                "prompt_topic": voice_bio.prompt_topic,
                "transcription": voice_bio.transcription,
                "status": voice_bio.status,
                "spectrogram": analysis["spectrogram"]
            },
            "acoustic_analysis": {
                "fundamental_frequency_hz": analysis["pitch_f0"],
                "resonance_frequency_hz": analysis["resonance_frequency_hz"],
                "timbre_warmth": analysis["timbre_warmth"],
                "harmonic_interval": analysis["harmonic_interval"],
                "duration_sec": analysis["duration_sec"]
            }
        }
    except Exception as e:
        session.rollback()
        response.status_code = 500
        return {"success": False, "error": str(e), "message": "Не удалось обработать аудио-визитку."}
    finally:
        session.close()


@app.get("/api/voice/{identifier}")
def get_user_voice_bio(identifier: str, request: Request, response: Response):
    """Returns active voice bio with spectrogram and acoustic analysis for user."""
    session = SyncSessionLocal()
    try:
        user = None
        if identifier == "me":
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                payload = verify_access_token(auth_header.split(" ")[1])
                if payload:
                    user = session.query(User).filter(User.id == payload.get("sub")).first()
            elif "resonance_session" in request.cookies:
                payload = verify_access_token(request.cookies.get("resonance_session"))
                if payload:
                    user = session.query(User).filter(User.id == payload.get("sub")).first()
        elif identifier.isdigit():
            user = session.query(User).filter(User.id == int(identifier)).first()
        else:
            user = session.query(User).filter(User.email.ilike(identifier)).first()

        if not user:
            response.status_code = 404
            return {"success": False, "message": "Пользователь не найден"}

        if not user.voice_bio:
            return {"success": True, "voice_bio": None, "message": "Голосовая визитка пока не записана"}

        spectrogram = []
        if user.voice_bio.spectrogram_json:
            try:
                spectrogram = json.loads(user.voice_bio.spectrogram_json)
            except Exception:
                pass

        return {
            "success": True,
            "voice_bio": {
                "id": user.voice_bio.id,
                "user_id": user.id,
                "audio_file": user.voice_bio.audio_file,
                "duration_sec": user.voice_bio.duration_sec,
                "pitch_f0": user.voice_bio.pitch_f0,
                "prompt_topic": user.voice_bio.prompt_topic or "О чем я могу говорить часами без остановки",
                "transcription": user.voice_bio.transcription,
                "status": user.voice_bio.status,
                "spectrogram": spectrogram
            }
        }
    finally:
        session.close()


@app.api_route("/index.html", methods=["GET", "HEAD"])
async def index_page():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


@app.api_route("/profile.html", methods=["GET", "HEAD"])
@app.api_route("/profile", methods=["GET", "HEAD"])
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
