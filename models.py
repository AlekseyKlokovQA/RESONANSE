"""
SQLAlchemy Database Models for Resonance Club Platform
Compliant with 09_TECH_STACK_AND_DATABASE_SCHEMA.md
Optimized for FastAPI + SQLAdmin auto-generation.
"""

import hashlib
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, Date, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(128), nullable=False, index=True)
    phone = Column(String(32), nullable=False, unique=True, index=True)
    email = Column(String(128), nullable=False, unique=True, index=True)
    gender = Column(String(16), nullable=False, default="Мужчина")  # Мужчина, Женщина
    target_gender = Column(String(16), nullable=False, default="Женщина")  # Женщина, Мужчина, Любой
    goal = Column(String(64), nullable=False, default="Глубокие отношения")
    status = Column(String(32), nullable=False, default="waitlist")  # waitlist, verified_member, suspended, alumni
    role = Column(String(32), nullable=False, default="resident")  # resident, candidate, concierge, superadmin
    password_hash = Column(String(256), nullable=False, default="")
    plain_password = Column(String(128), nullable=True)  # For demo inspection & concierge verification
    vip_pass_code = Column(String(32), nullable=False, unique=True, index=True)
    reputation_score = Column(Float, nullable=False, default=5.00)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="joined")
    voice_bio = relationship("VoiceBio", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="joined")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.plain_password = password
        self.password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return self.password_hash == hashlib.sha256(password.encode("utf-8")).hexdigest()

    def __str__(self):
        return f"{self.full_name} ({self.vip_pass_code})"


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    age = Column(Integer, nullable=False)
    city = Column(String(64), nullable=False, default="Москва")
    occupation = Column(String(128), nullable=False)
    bio = Column(Text, nullable=True)
    archetype = Column(String(64), nullable=False, default="Мудрец • Архитектор")
    acoustic_frequency_hz = Column(Integer, nullable=False, default=432)
    photos_unlocked = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile", lazy="joined")

    def __str__(self):
        return f"Профиль #{self.id} ({self.city}, {self.age} лет)"


class VoiceBio(Base):
    __tablename__ = "voice_bios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    audio_file = Column(String(255), nullable=False)  # e.g. /alexander_voice.mp3
    duration_sec = Column(Integer, nullable=False, default=24)
    transcription = Column(Text, nullable=True)
    pitch_f0 = Column(Float, nullable=False, default=128.5)
    status = Column(String(32), nullable=False, default="pending")  # pending, verified, rejected
    verified_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="voice_bio", lazy="joined")

    def __str__(self):
        return f"Визитка #{self.id} [{self.status}]"


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question_number = Column(Integer, nullable=False, unique=True, index=True)
    category = Column(String(64), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    polarity = Column(String(32), nullable=True)
    weight = Column(Float, nullable=False, default=1.0)

    def __str__(self):
        return f"№{self.question_number}. [{self.category}] {self.question_text[:40]}..."


class WeeklyMatch(Base):
    __tablename__ = "weekly_matches"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    match_date = Column(Date, nullable=False, default=datetime.utcnow().date)
    resonance_score = Column(Integer, nullable=False, default=90)  # Percent 0-100%
    status = Column(String(32), nullable=False, default="active_24h")  # active_24h, booked, completed, expired
    expires_at = Column(DateTime, nullable=False)

    user1 = relationship("User", foreign_keys=[user1_id], lazy="joined")
    user2 = relationship("User", foreign_keys=[user2_id], lazy="joined")
    booking = relationship("DateBooking", back_populates="match", uselist=False, cascade="all, delete-orphan")

    def __str__(self):
        return f"Пара #{self.id} ({self.resonance_score}% Созвучие)"


class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, index=True)
    city = Column(String(64), nullable=False, default="Москва")
    address = Column(String(255), nullable=False)
    rating = Column(Float, nullable=False, default=4.9)
    cuisine = Column(String(128), nullable=False)
    average_check = Column(Integer, nullable=False, default=4000)
    club_perk = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    bookings = relationship("DateBooking", back_populates="venue")

    def __str__(self):
        return f"{self.name} ({self.city}, ★ {self.rating})"


class DateBooking(Base):
    __tablename__ = "date_bookings"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("weekly_matches.id", ondelete="CASCADE"), nullable=False, unique=True)
    venue_id = Column(Integer, ForeignKey("venues.id", ondelete="RESTRICT"), nullable=False)
    booking_time = Column(DateTime, nullable=False)
    guests_count = Column(Integer, nullable=False, default=2)
    status = Column(String(32), nullable=False, default="reserved")  # reserved, confirmed, completed, cancelled
    deposit_amount = Column(Integer, nullable=False, default=3000)

    match = relationship("WeeklyMatch", back_populates="booking", lazy="joined")
    venue = relationship("Venue", back_populates="bookings", lazy="joined")

    def __str__(self):
        return f"Бронь #{self.id} [{self.status}]"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tier = Column(String(64), nullable=False, default="Стандарт (1 490 ₽/мес)")
    amount = Column(Integer, nullable=False, default=1490)
    is_active = Column(Boolean, nullable=False, default=True)
    valid_until = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="subscriptions", lazy="joined")

    def __str__(self):
        return f"Подписка #{self.id} — {self.tier}"
