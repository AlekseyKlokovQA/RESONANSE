"""
SQLAdmin ModelViews configured for Resonance Club Platform
Provides automatic CRUD generation, localized labels, and in-table HTML5 audio players.
"""

import random
import datetime
from markupsafe import Markup
from sqladmin import ModelView, action
from starlette.requests import Request
from starlette.responses import RedirectResponse
from sqlalchemy import select
from database import AsyncSessionLocal
from sqladmin.filters import AllUniqueStringValuesFilter, BooleanFilter
from models import (
    User, Profile, VoiceBio, Question, WeeklyMatch, Venue, DateBooking, Subscription
)


class UserAdmin(ModelView, model=User):
    name = "Резидент"
    name_plural = "Резиденты и Очередь"
    icon = "fa-solid fa-users"
    category = "Клуб и Резиденты"

    page_size = 50
    page_size_options = [20, 50, 100]
    column_default_sort = [(User.id, True)]

    column_list = [
        User.id,
        User.full_name,
        User.role,
        User.status,
        User.email,
        User.gender,
        User.vip_pass_code,
        User.phone,
        User.reputation_score,
        User.created_at
    ]

    column_searchable_list = [User.full_name, User.phone, User.email, User.vip_pass_code, User.role]
    column_sortable_list = [User.id, User.full_name, User.role, User.reputation_score, User.created_at]
    column_filters = [
        AllUniqueStringValuesFilter(User.role),
        AllUniqueStringValuesFilter(User.gender),
        AllUniqueStringValuesFilter(User.status)
    ]

    column_labels = {
        User.id: "ID",
        User.full_name: "ФИО Резидента",
        User.role: "Роль в системе",
        User.gender: "Пол",
        User.target_gender: "Кого ищет",
        User.goal: "Цель вступления",
        User.status: "Статус в клубе",
        User.vip_pass_code: "VIP-код пропуска",
        User.phone: "Телефон",
        User.email: "Электронная почта",
        User.plain_password: "Демо-пароль",
        User.reputation_score: "Рейтинг",
        User.created_at: "Дата заявки"
    }

    @action(
        name="approve_candidate",
        label="✓ Принять в клуб",
        confirmation_message="Вы уверены, что хотите ПРИНЯТЬ выбранных кандидатов в резиденты Клуба?",
        add_in_detail=True,
        add_in_list=True
    )
    async def approve_candidate(self, request: Request) -> RedirectResponse:
        pks = [int(pk) for pk in request.query_params.get("pks", "").split(",") if pk.isdigit()]
        if pks:
            async with AsyncSessionLocal() as session:
                stmt = select(User).where(User.id.in_(pks))
                result = await session.execute(stmt)
                users = result.scalars().all()
                for u in users:
                    u.status = "verified_member"
                    u.role = "resident"
                    if not u.vip_pass_code or "WAIT" in u.vip_pass_code:
                        u.vip_pass_code = f"RES-{random.randint(1000, 9999)}-VIP"
                await session.commit()
        referer = request.headers.get("referer") or "/admin/user/list"
        return RedirectResponse(url=referer, status_code=303)

    @action(
        name="reject_candidate",
        label="✕ Отклонить заявку",
        confirmation_message="Вы уверены, что хотите ОТКЛОНИТЬ заявку выбранных кандидатов?",
        add_in_detail=True,
        add_in_list=True
    )
    async def reject_candidate(self, request: Request) -> RedirectResponse:
        pks = [int(pk) for pk in request.query_params.get("pks", "").split(",") if pk.isdigit()]
        if pks:
            async with AsyncSessionLocal() as session:
                stmt = select(User).where(User.id.in_(pks))
                result = await session.execute(stmt)
                users = result.scalars().all()
                for u in users:
                    u.status = "rejected"
                await session.commit()
        referer = request.headers.get("referer") or "/admin/user/list"
        return RedirectResponse(url=referer, status_code=303)

    column_formatters = {
        User.role: lambda m, a: Markup(
            '<span class="badge bg-warning text-dark fw-bold px-2 py-1">👑 Superadmin</span>'
            if m.role == "superadmin"
            else '<span class="badge bg-purple text-white px-2 py-1" style="background:#8B5CF6!important">💎 Резидент</span>'
            if m.role == "resident"
            else '<span class="badge bg-info text-white px-2 py-1">⏳ Кандидат</span>'
            if m.role == "candidate"
            else f'<span class="badge bg-secondary">{m.role}</span>'
        ),
        User.status: lambda m, a: Markup(
            f'''
            <div style="display:flex; flex-direction:column; gap:4px;">
                <div>
                    <span class="badge-status badge-waitlist">⏳ Лист ожидания</span>
                </div>
                <div class="d-flex align-items-center gap-1 mt-1">
                    <a href="/admin/user/action/approve-candidate?pks={m.id}" class="btn btn-sm btn-success py-0 px-2" style="font-size: 11px; text-decoration: none;" title="Принять заявку в клуб">✓ Принять</a>
                    <a href="/admin/user/action/reject-candidate?pks={m.id}" class="btn btn-sm btn-outline-danger py-0 px-2" style="font-size: 11px; text-decoration: none;" title="Отклонить заявку">✕ Отклонить</a>
                </div>
            </div>
            '''
            if m.status == "waitlist"
            else f'''
            <div style="display:flex; align-items:center; gap:6px;">
                <span class="badge-status badge-verified">✓ Верифицирован (VIP)</span>
                <a href="/admin/user/action/reject-candidate?pks={m.id}" class="btn btn-sm btn-link text-danger p-0" style="font-size: 10px; text-decoration: none;" title="Отозвать и отклонить заявку">Отклонить</a>
            </div>
            '''
            if m.status == "verified_member"
            else f'''
            <div style="display:flex; align-items:center; gap:6px;">
                <span class="badge-status badge-rejected">✕ Отклонен</span>
                <a href="/admin/user/action/approve-candidate?pks={m.id}" class="btn btn-sm btn-link text-success p-0" style="font-size: 10px; text-decoration: none;" title="Принять в клуб">Принять</a>
            </div>
            '''
            if m.status == "rejected"
            else f'<span class="badge-status">{m.status}</span>'
        ),
        User.vip_pass_code: lambda m, a: Markup(
            f'<span class="code-vip">{m.vip_pass_code}</span>'
        ),
        User.reputation_score: lambda m, a: Markup(
            f'<span class="rating-gold">★ {m.reputation_score:.2f}</span>'
        )
    }


class ProfileAdmin(ModelView, model=Profile):
    name = "Психологический профиль"
    name_plural = "Профили Резидентов"
    icon = "fa-solid fa-id-badge"
    category = "Клуб и Резиденты"

    page_size = 50
    page_size_options = [20, 50, 100]
    column_default_sort = [(Profile.id, True)]

    column_list = [
        Profile.id,
        Profile.user,
        Profile.age,
        Profile.city,
        Profile.occupation,
        Profile.archetype,
        Profile.acoustic_frequency_hz,
        Profile.photos_unlocked
    ]

    column_searchable_list = [Profile.city, Profile.occupation, Profile.archetype]
    column_filters = [BooleanFilter(Profile.photos_unlocked)]

    column_labels = {
        Profile.id: "ID",
        Profile.user: "Резидент",
        Profile.age: "Возраст",
        Profile.city: "Город",
        Profile.occupation: "Деятельность & Призвание",
        Profile.bio: "О себе и ценностях",
        Profile.archetype: "Психологический архетип",
        Profile.acoustic_frequency_hz: "Частота созвучия",
        Profile.photos_unlocked: "Вуаль фото",
        Profile.updated_at: "Обновлен"
    }

    column_formatters = {
        Profile.acoustic_frequency_hz: lambda m, a: Markup(
            f'<span class="badge-freq">{m.acoustic_frequency_hz} Гц</span>'
        ),
        Profile.photos_unlocked: lambda m, a: Markup(
            '<span class="badge-status badge-verified">🔓 Вуаль снята</span>'
            if m.photos_unlocked
            else '<span class="badge-status badge-waitlist">🔒 Вуаль активна</span>'
        )
    }


class VoiceBioAdmin(ModelView, model=VoiceBio):
    name = "Аудио-визитка"
    name_plural = "Модерация Аудио-визиток"
    icon = "fa-solid fa-microphone-lines"
    category = "Клуб и Резиденты"

    page_size = 50
    page_size_options = [20, 50, 100]
    column_default_sort = [(VoiceBio.id, True)]

    column_list = [
        VoiceBio.id,
        VoiceBio.user,
        VoiceBio.audio_file,
        VoiceBio.prompt_topic,
        VoiceBio.duration_sec,
        VoiceBio.pitch_f0,
        VoiceBio.status,
        VoiceBio.verified_at
    ]

    column_filters = [AllUniqueStringValuesFilter(VoiceBio.status)]
    column_searchable_list = [VoiceBio.prompt_topic, VoiceBio.transcription]
    column_sortable_list = [VoiceBio.id, VoiceBio.duration_sec, VoiceBio.pitch_f0, VoiceBio.status]

    column_labels = {
        VoiceBio.id: "ID",
        VoiceBio.user: "Кандидат / Резидент",
        VoiceBio.audio_file: "Прослушать визитку",
        VoiceBio.prompt_topic: "Тема визитки",
        VoiceBio.duration_sec: "Длительность",
        VoiceBio.transcription: "Расшифровка речи (STT Whisper)",
        VoiceBio.pitch_f0: "Тон F0",
        VoiceBio.status: "Статус модерации",
        VoiceBio.verified_at: "Дата проверки"
    }

    @action(
        name="approve_voice",
        label="✓ Принять визитку",
        confirmation_message="Вы уверены, что хотите ПРИНЯТЬ выбранные аудиовизитки?",
        add_in_detail=True,
        add_in_list=True
    )
    async def approve_voice(self, request: Request) -> RedirectResponse:
        pks = [int(pk) for pk in request.query_params.get("pks", "").split(",") if pk.isdigit()]
        if pks:
            async with AsyncSessionLocal() as session:
                stmt = select(VoiceBio).where(VoiceBio.id.in_(pks))
                result = await session.execute(stmt)
                bios = result.scalars().all()
                for b in bios:
                    b.status = "verified"
                    b.verified_at = datetime.datetime.now(datetime.timezone.utc)
                await session.commit()
        referer = request.headers.get("referer") or "/admin/voice-bio/list"
        return RedirectResponse(url=referer, status_code=303)

    @action(
        name="reject_voice",
        label="✕ Отклонить визитку",
        confirmation_message="Вы уверены, что хотите ОТКЛОНИТЬ выбранные аудиовизитки?",
        add_in_detail=True,
        add_in_list=True
    )
    async def reject_voice(self, request: Request) -> RedirectResponse:
        pks = [int(pk) for pk in request.query_params.get("pks", "").split(",") if pk.isdigit()]
        if pks:
            async with AsyncSessionLocal() as session:
                stmt = select(VoiceBio).where(VoiceBio.id.in_(pks))
                result = await session.execute(stmt)
                bios = result.scalars().all()
                for b in bios:
                    b.status = "rejected"
                await session.commit()
        referer = request.headers.get("referer") or "/admin/voice-bio/list"
        return RedirectResponse(url=referer, status_code=303)

    column_formatters = {
        VoiceBio.audio_file: lambda m, a: Markup(
            f'''
            <div class="audio-table-cell">
                <audio controls preload="none" style="height:32px; width:220px; outline:none;">
                    <source src="/{m.audio_file.lstrip('/')}">
                    Ваш браузер не поддерживает аудио.
                </audio>
            </div>
            '''
        ),
        VoiceBio.duration_sec: lambda m, a: f"{m.duration_sec} сек.",
        VoiceBio.pitch_f0: lambda m, a: Markup(
            f'<span class="badge-pitch">{m.pitch_f0:.1f} Гц</span>'
        ),
        VoiceBio.status: lambda m, a: Markup(
            f'''
            <div style="display:flex; flex-direction:column; gap:4px;">
                <span class="badge-status badge-pending">● На модерации</span>
                <div class="d-flex align-items-center gap-1 mt-1">
                    <a href="/admin/voice-bio/action/approve-voice?pks={m.id}" class="btn btn-sm btn-success py-0 px-2" style="font-size: 11px; text-decoration: none;" title="Принять визитку">✓ Принять</a>
                    <a href="/admin/voice-bio/action/reject-voice?pks={m.id}" class="btn btn-sm btn-outline-danger py-0 px-2" style="font-size: 11px; text-decoration: none;" title="Отклонить визитку">✕ Отклонить</a>
                </div>
            </div>
            '''
            if m.status == "pending"
            else f'''
            <div style="display:flex; align-items:center; gap:6px;">
                <span class="badge-status badge-verified">✓ Принято</span>
                <a href="/admin/voice-bio/action/reject-voice?pks={m.id}" class="btn btn-sm btn-link text-danger p-0" style="font-size: 10px; text-decoration: none;">Отклонить</a>
            </div>
            '''
            if m.status == "verified"
            else f'''
            <div style="display:flex; align-items:center; gap:6px;">
                <span class="badge-status badge-rejected">✕ Отклонено</span>
                <a href="/admin/voice-bio/action/approve-voice?pks={m.id}" class="btn btn-sm btn-link text-success p-0" style="font-size: 10px; text-decoration: none;">Принять</a>
            </div>
            '''
            if m.status == "rejected"
            else f'<span class="badge-status">{m.status}</span>'
        )
    }


class WeeklyMatchAdmin(ModelView, model=WeeklyMatch):
    name = "Матч четверга"
    name_plural = "Пары Четверга (Матчинг)"
    icon = "fa-solid fa-heart"
    category = "Матчинг и Свидания"

    column_list = [
        WeeklyMatch.id,
        WeeklyMatch.user1,
        WeeklyMatch.user2,
        WeeklyMatch.resonance_score,
        WeeklyMatch.status,
        WeeklyMatch.match_date,
        WeeklyMatch.expires_at
    ]

    column_filters = [AllUniqueStringValuesFilter(WeeklyMatch.status)]
    column_labels = {
        WeeklyMatch.id: "ID",
        WeeklyMatch.user1: "Кандидат А",
        WeeklyMatch.user2: "Кандидат Б",
        WeeklyMatch.match_date: "Дата подбора",
        WeeklyMatch.resonance_score: "Созвучие ценностей",
        WeeklyMatch.status: "Статус окна чата",
        WeeklyMatch.expires_at: "Окончание 24ч окна"
    }

    column_formatters = {
        WeeklyMatch.resonance_score: lambda m, a: Markup(
            f'<span class="resonance-badge-gold">✦ {m.resonance_score}% Созвучие</span>'
        ),
        WeeklyMatch.status: lambda m, a: Markup(
            '<span class="badge-status badge-active-pulse">● 24ч окно активно</span>'
            if m.status == "active_24h"
            else '<span class="badge-status badge-booked">🍷 Свидание назначено</span>'
            if m.status == "booked"
            else f'<span class="badge-status">{m.status}</span>'
        )
    }


class VenueAdmin(ModelView, model=Venue):
    name = "Ресторан-партнер"
    name_plural = "Партнерские Рестораны"
    icon = "fa-solid fa-utensils"
    category = "Матчинг и Свидания"

    column_list = [
        Venue.id,
        Venue.name,
        Venue.city,
        Venue.rating,
        Venue.cuisine,
        Venue.average_check,
        Venue.is_active
    ]

    column_searchable_list = [Venue.name, Venue.city, Venue.cuisine]
    column_filters = [BooleanFilter(Venue.is_active)]

    column_labels = {
        Venue.id: "ID",
        Venue.name: "Название заведения",
        Venue.city: "Город",
        Venue.address: "Адрес",
        Venue.rating: "Рейтинг",
        Venue.cuisine: "Кухня / Концепция",
        Venue.average_check: "Средний чек",
        Venue.club_perk: "Клубный комплимент",
        Venue.is_active: "Сотрудничество активно"
    }

    column_formatters = {
        Venue.rating: lambda m, a: Markup(
            f'<span class="rating-gold">★ {m.rating:.2f}</span>'
        ),
        Venue.average_check: lambda m, a: f"{m.average_check:,} ₽".replace(",", " "),
        Venue.is_active: lambda m, a: Markup(
            '<span class="badge-status badge-verified">✓ Активен</span>'
            if m.is_active else '<span class="badge-status badge-rejected">Приостановлен</span>'
        )
    }


class DateBookingAdmin(ModelView, model=DateBooking):
    name = "Бронь свидания"
    name_plural = "Бронирования Консьержа"
    icon = "fa-solid fa-champagne-glasses"
    category = "Матчинг и Свидания"

    column_list = [
        DateBooking.id,
        DateBooking.match,
        DateBooking.venue,
        DateBooking.booking_time,
        DateBooking.status,
        DateBooking.deposit_amount
    ]

    column_filters = [AllUniqueStringValuesFilter(DateBooking.status)]
    column_labels = {
        DateBooking.id: "ID",
        DateBooking.match: "Пара (Матч)",
        DateBooking.venue: "Ресторан",
        DateBooking.booking_time: "Время брони",
        DateBooking.guests_count: "Персон",
        DateBooking.status: "Статус брони",
        DateBooking.deposit_amount: "Депозит клуба"
    }

    column_formatters = {
        DateBooking.deposit_amount: lambda m, a: f"{m.deposit_amount:,} ₽".replace(",", " "),
        DateBooking.status: lambda m, a: Markup(
            '<span class="badge-status badge-verified">✓ Подтверждено</span>'
            if m.status == "confirmed"
            else '<span class="badge-status badge-pending">Зарезервировано</span>'
            if m.status == "reserved"
            else f'<span class="badge-status">{m.status}</span>'
        )
    }


class QuestionAdmin(ModelView, model=Question):
    name = "Вопрос анкеты"
    name_plural = "Банк 100 Вопросов"
    icon = "fa-solid fa-clipboard-question"
    category = "Методология и Психология"

    column_list = [
        Question.question_number,
        Question.category,
        Question.question_text,
        Question.polarity,
        Question.weight
    ]

    column_searchable_list = [Question.question_text, Question.category, Question.option_a, Question.option_b]
    column_filters = [AllUniqueStringValuesFilter(Question.category)]

    column_labels = {
        Question.id: "ID",
        Question.question_number: "№",
        Question.category: "Психологическая сфера",
        Question.question_text: "Формулировка дилеммы",
        Question.option_a: "Полюс А (Вариант 1)",
        Question.option_b: "Полюс Б (Вариант 2)",
        Question.polarity: "Шкала полярности",
        Question.weight: "Вес в алгоритме"
    }

    column_formatters = {
        Question.question_number: lambda m, a: Markup(
            f'<span class="badge-question-num">№{m.question_number:02d}</span>'
        ),
        Question.category: lambda m, a: Markup(
            f'<span class="badge-category">{m.category}</span>'
        )
    }


class SubscriptionAdmin(ModelView, model=Subscription):
    name = "Подписка"
    name_plural = "Членские Взносы & VIP"
    icon = "fa-solid fa-crown"
    category = "Финансы и Членство"

    column_list = [
        Subscription.id,
        Subscription.user,
        Subscription.tier,
        Subscription.amount,
        Subscription.is_active,
        Subscription.valid_until
    ]

    column_labels = {
        Subscription.id: "ID",
        Subscription.user: "Резидент",
        Subscription.tier: "Тарифный план",
        Subscription.amount: "Сумма",
        Subscription.is_active: "Статус",
        Subscription.valid_until: "Действует до",
        Subscription.created_at: "Дата оформления"
    }

    column_formatters = {
        Subscription.amount: lambda m, a: f"{m.amount:,} ₽".replace(",", " "),
        Subscription.is_active: lambda m, a: Markup(
            '<span class="badge-status badge-verified">Активна</span>'
            if m.is_active else '<span class="badge-status badge-rejected">Истекла</span>'
        )
    }
