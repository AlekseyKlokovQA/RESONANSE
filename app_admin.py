"""
Resonance Club Platform — FastAPI + SQLAdmin Application (v1.0.2)
Automatically generates full CRUD tables and forms from SQLAlchemy models.
"""

import os
import sys
import argparse
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
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


@app.api_route("/index.html", methods=["GET", "HEAD"])
async def index_page():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


@app.api_route("/profile.html", methods=["GET", "HEAD"])
async def profile_page():
    return FileResponse(os.path.join(BASE_DIR, "profile.html"))


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
