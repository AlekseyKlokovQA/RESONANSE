"""
Seed database with realistic initial data for Resonance Club
Includes 100 questions from questions_100.json, verified members, waitlist applicants,
venues, matches, and bookings.
"""

import os
import json
from datetime import datetime, timedelta, timezone
from database import init_db, SyncSessionLocal
from models import (
    User, Profile, VoiceBio, Question, WeeklyMatch, Venue, DateBooking, Subscription
)


def seed_database():
    init_db()
    session = SyncSessionLocal()

    # Check if database is already seeded
    if session.query(User).count() > 0:
        print("Database already contains data, skipping seed.")
        session.close()
        return

    print("Seeding questions from questions_100.json...")
    questions_file = os.path.join(os.path.dirname(__file__), "questions_100.json")
    if os.path.exists(questions_file):
        with open(questions_file, "r", encoding="utf-8") as f:
            questions_data = json.load(f)

        for q in questions_data:
            question_obj = Question(
                question_number=q.get("id"),
                category=q.get("category", "Ценности"),
                question_text=q.get("question", ""),
                option_a=q.get("option_a", ""),
                option_b=q.get("option_b", ""),
                polarity=q.get("scale", "Двойственная"),
                weight=1.0
            )
            session.add(question_obj)
        session.commit()
        print(f"Loaded {len(questions_data)} psychological questions.")

    print("Seeding verified candidate members...")
    candidates = [
        {
            "full_name": "Александр Волков",
            "phone": "+7 (916) 432-88-12",
            "email": "alexander.volkov@resonance.club",
            "gender": "Мужчина",
            "target_gender": "Женщина",
            "goal": "Глубокие отношения",
            "status": "verified_member",
            "vip_pass_code": "RES-8841-VIP",
            "reputation_score": 5.0,
            "age": 31,
            "city": "Москва",
            "occupation": "Архитектор сложных систем & Яхтсмен",
            "bio": "Ищу человека, с которым молчание наполнено смыслом больше, чем тысячи пустых слов. Ценю внутреннюю автономию, ночное море и тонкую иронию.",
            "archetype": "Мудрец • Архитектор",
            "acoustic_frequency_hz": 432,
            "photos_unlocked": True,
            "audio_file": "alexander_voice.mp3",
            "duration_sec": 24,
            "transcription": "«Для меня настоящая близость начинается там, где исчезает необходимость казаться кем-то другим. В людях ищу внутренний стержень и способность к глубокой тишине...»",
            "pitch_f0": 118.4,
            "sub_tier": "VIP Concierge (4 900 ₽/мес)",
            "sub_amount": 4900
        },
        {
            "full_name": "Анна Соколова",
            "phone": "+7 (925) 528-11-90",
            "email": "anna.sokolova@resonance.club",
            "gender": "Женщина",
            "target_gender": "Мужчина",
            "goal": "Глубокие отношения",
            "status": "verified_member",
            "vip_pass_code": "RES-5283-VIP",
            "reputation_score": 4.98,
            "age": 28,
            "city": "Москва",
            "occupation": "Арт-директор бюро пространств",
            "bio": "Создаю атмосферу и архитектуру света. Верю, что красота кроется в деталях и честности перед собой. Мечтаю о партнере для интеллектуальных путешествий.",
            "archetype": "Творец • Эстет",
            "acoustic_frequency_hz": 528,
            "photos_unlocked": True,
            "audio_file": "anna_voice.mp3",
            "duration_sec": 21,
            "transcription": "«Красота для меня — это не глянец, а органичность. Когда человек говорит искренне, в голосе звучит совсем другая мелодика. Хочется встретить того, кто слышит мир так же...»",
            "pitch_f0": 212.8,
            "sub_tier": "Стандарт (1 490 ₽/мес)",
            "sub_amount": 1490
        },
        {
            "full_name": "София Мельникова",
            "phone": "+7 (903) 741-33-55",
            "email": "sofia.m@resonance.club",
            "gender": "Женщина",
            "target_gender": "Мужчина",
            "goal": "Интеллектуальный союз",
            "status": "verified_member",
            "vip_pass_code": "RES-3965-VIP",
            "reputation_score": 4.95,
            "age": 26,
            "city": "Москва",
            "occupation": "Исследователь когнитивистики & Пианистка",
            "bio": "Изучаю природу восприятия и феноменологию сознания. В отношениях важен резонанс ценностей и способность к открытому диалогу без масок.",
            "archetype": "Мудрец • Мыслитель",
            "acoustic_frequency_hz": 396,
            "photos_unlocked": False,
            "audio_file": "sofia_voice.mp3",
            "duration_sec": 26,
            "transcription": "«Музыка и когнитивные науки научили меня главному — мы сотканы из резонансов. Если базовая тональность совпадает, всё остальное складывается гармонично...»",
            "pitch_f0": 224.5,
            "sub_tier": "VIP Concierge (4 900 ₽/мес)",
            "sub_amount": 4900
        },
        {
            "full_name": "Полина Рейн",
            "phone": "+7 (981) 639-44-22",
            "email": "polina.reyn@resonance.club",
            "gender": "Женщина",
            "target_gender": "Мужчина",
            "goal": "Глубокие отношения",
            "status": "verified_member",
            "vip_pass_code": "RES-6391-VIP",
            "reputation_score": 4.92,
            "age": 29,
            "city": "Санкт-Петербург",
            "occupation": "Нейробиолог & Альпинистка",
            "bio": "Исследую нейронные сети и горные вершины. Люблю долгие разговоры у камина, чистый воздух и верность собственному слову.",
            "archetype": "Искатель • Новатор",
            "acoustic_frequency_hz": 639,
            "photos_unlocked": False,
            "audio_file": "polina_voice.mp3",
            "duration_sec": 22,
            "transcription": "«В горах цена ошибки слишком высока, поэтому я привыкла доверять действиям, а не обещаниям. Ищу человека со здоровым азартом и теплым сердцем...»",
            "pitch_f0": 208.1,
            "sub_tier": "Стандарт (1 490 ₽/мес)",
            "sub_amount": 1490
        },
        {
            "full_name": "Елена Романова",
            "phone": "+7 (915) 852-77-66",
            "email": "elena.romanova@resonance.club",
            "gender": "Женщина",
            "target_gender": "Мужчина",
            "goal": "Создание семьи",
            "status": "verified_member",
            "vip_pass_code": "RES-8524-VIP",
            "reputation_score": 5.0,
            "age": 27,
            "city": "Москва",
            "occupation": "Куратор музейных выставок",
            "bio": "Курирую международные арт-проекты. Ценю душевную щедрость, культуру диалога и умение ценить тихие радости каждого дня.",
            "archetype": "Эстет • Хранитель",
            "acoustic_frequency_hz": 528,
            "photos_unlocked": False,
            "audio_file": "elena_voice.mp3",
            "duration_sec": 25,
            "transcription": "«Искусство для меня — это зеркало души. В отношениях ценю искреннее бережное отношение и умение слушать другого без осуждения...»",
            "pitch_f0": 218.9,
            "sub_tier": "VIP Concierge (4 900 ₽/мес)",
            "sub_amount": 4900
        }
    ]

    saved_users = {}
    now = datetime.now(timezone.utc)

    for c in candidates:
        user = User(
            full_name=c["full_name"],
            phone=c["phone"],
            email=c["email"],
            gender=c["gender"],
            target_gender=c["target_gender"],
            goal=c["goal"],
            status=c["status"],
            vip_pass_code=c["vip_pass_code"],
            reputation_score=c["reputation_score"],
            created_at=now - timedelta(days=15)
        )
        session.add(user)
        session.flush()
        saved_users[c["full_name"]] = user

        profile = Profile(
            user_id=user.id,
            age=c["age"],
            city=c["city"],
            occupation=c["occupation"],
            bio=c["bio"],
            archetype=c["archetype"],
            acoustic_frequency_hz=c["acoustic_frequency_hz"],
            photos_unlocked=c["photos_unlocked"]
        )
        session.add(profile)

        voice = VoiceBio(
            user_id=user.id,
            audio_file=c["audio_file"],
            duration_sec=c["duration_sec"],
            transcription=c["transcription"],
            pitch_f0=c["pitch_f0"],
            status="verified",
            verified_at=now - timedelta(days=14)
        )
        session.add(voice)

        sub = Subscription(
            user_id=user.id,
            tier=c["sub_tier"],
            amount=c["sub_amount"],
            is_active=True,
            valid_until=now + timedelta(days=25)
        )
        session.add(sub)

    print("Seeding waitlist applicants for moderation...")
    waitlist_users = [
        {
            "full_name": "Максим Белов",
            "phone": "+7 (905) 112-99-88",
            "email": "maxim.belov@resonance.club",
            "gender": "Мужчина",
            "target_gender": "Женщина",
            "goal": "Глубокие отношения",
            "status": "waitlist",
            "vip_pass_code": "RES-7104-WAIT",
            "reputation_score": 5.0,
            "age": 34,
            "city": "Москва",
            "occupation": "Основатель EdTech платформы",
            "bio": "Люблю сложные книги, горные лыжи и вечерние прогулки по бульварам. Ищу союз равных умов.",
            "archetype": "Правитель • Новатор",
            "acoustic_frequency_hz": 432,
            "audio_file": "alexander_voice.mp3",
            "duration_sec": 24,
            "transcription": "«Привет! Хочу вступить в клуб, потому что устал от бесконечных бессмысленных свайпов. Ищу глубину и честный диалог...»",
            "pitch_f0": 122.0
        },
        {
            "full_name": "Дарья Григорьева",
            "phone": "+7 (926) 334-55-11",
            "email": "daria.g@resonance.club",
            "gender": "Женщина",
            "target_gender": "Мужчина",
            "goal": "Создание семьи",
            "status": "waitlist",
            "vip_pass_code": "RES-8921-WAIT",
            "reputation_score": 5.0,
            "age": 28,
            "city": "Москва",
            "occupation": "Архитектор ландшафтов & Ботаник",
            "bio": "Создаю японские сады камней и закрытые оранжереи. Люблю природу, уютные интерьеры и искренних людей.",
            "archetype": "Творец • Хранитель",
            "acoustic_frequency_hz": 528,
            "audio_file": "anna_voice.mp3",
            "duration_sec": 20,
            "transcription": "«Здравствуйте! Для меня голос говорит о человеке в сто раз больше, чем отфотошопленная фотография. Надеюсь на скорое вступление в клуб...»",
            "pitch_f0": 215.3
        },
        {
            "full_name": "Дмитрий Морозов",
            "phone": "+7 (917) 888-44-33",
            "email": "dmitry.m@resonance.club",
            "gender": "Мужчина",
            "target_gender": "Женщина",
            "goal": "Интеллектуальный союз",
            "status": "waitlist",
            "vip_pass_code": "RES-9411-WAIT",
            "reputation_score": 5.0,
            "age": 32,
            "city": "Санкт-Петербург",
            "occupation": "Врач-нейрохирург",
            "bio": "Спасаю жизни в операционной. Вне работы люблю джаз, винил и шахматы.",
            "archetype": "Мудрец • Исцелитель",
            "acoustic_frequency_hz": 432,
            "audio_file": "alexander_voice.mp3",
            "duration_sec": 23,
            "transcription": "«Добрый день. Ценю время и честность. Верю, что глубокая привязанность строится на общих ценностях и уважении...»",
            "pitch_f0": 115.8
        },
        {
            "full_name": "Екатерина Воронина",
            "phone": "+7 (903) 654-32-10",
            "email": "ekaterina.v@resonance.club",
            "gender": "Женщина",
            "target_gender": "Мужчина",
            "goal": "Глубокие отношения",
            "status": "waitlist",
            "vip_pass_code": "RES-4512-WAIT",
            "reputation_score": 5.0,
            "age": 27,
            "city": "Москва",
            "occupation": "Литературный переводчик с французского",
            "bio": "Перевожу философские романы и эссе. Люблю старые кофейни, артхаусное кино и долгие ночные разговоры.",
            "archetype": "Любящий • Эстет",
            "acoustic_frequency_hz": 528,
            "audio_file": "sofia_voice.mp3",
            "duration_sec": 25,
            "transcription": "«Очень близка концепция анти-свайпа. Хочется наконец-то общаться с человеком, а не с алгоритмом витрины...»",
            "pitch_f0": 219.0
        }
    ]

    for w in waitlist_users:
        user = User(
            full_name=w["full_name"],
            phone=w["phone"],
            email=w["email"],
            gender=w["gender"],
            target_gender=w["target_gender"],
            goal=w["goal"],
            status=w["status"],
            vip_pass_code=w["vip_pass_code"],
            reputation_score=w["reputation_score"],
            created_at=now - timedelta(hours=8)
        )
        session.add(user)
        session.flush()
        saved_users[w["full_name"]] = user

        profile = Profile(
            user_id=user.id,
            age=w["age"],
            city=w["city"],
            occupation=w["occupation"],
            bio=w["bio"],
            archetype=w["archetype"],
            acoustic_frequency_hz=w["acoustic_frequency_hz"],
            photos_unlocked=False
        )
        session.add(profile)

        voice = VoiceBio(
            user_id=user.id,
            audio_file=w["audio_file"],
            duration_sec=w["duration_sec"],
            transcription=w["transcription"],
            pitch_f0=w["pitch_f0"],
            status="pending",
            verified_at=None
        )
        session.add(voice)

    print("Seeding partner fine dining venues...")
    venues = [
        {
            "name": "Ресторан «Белуга»",
            "city": "Москва",
            "address": "ул. Моховая, 15/1, стр. 1 (Отель «Националь»)",
            "rating": 4.96,
            "cuisine": "Высокая русская / Деликатесы",
            "average_check": 6500,
            "club_perk": "Приватный угловой столик с панорамным видом на Кремль + авторский сет десертов от шеф-повара для резидентов клуба.",
            "is_active": True
        },
        {
            "name": "Grand Cru Wine & Dining",
            "city": "Москва",
            "address": "Малая Бронная ул., 22, стр. 2",
            "rating": 4.94,
            "cuisine": "Авторская винная гастрономия (Звезда Michelin)",
            "average_check": 5500,
            "club_perk": "Индивидуальный сомелье-пейринг и комплиментарные бокалы винтажного шампанского при подтверждении бронирования через консьержа.",
            "is_active": True
        },
        {
            "name": "Twins Garden",
            "city": "Москва",
            "address": "Страстной бульвар, 8А",
            "rating": 4.98,
            "cuisine": "Современная гастроботаника & Фермерские продукты",
            "average_check": 6000,
            "club_perk": "Тихая зона в зимнем саду, защита от постороннего шума, авторский гастрономический сюрприз для первой встречи.",
            "is_active": True
        },
        {
            "name": "Северяне (Severyane)",
            "city": "Москва",
            "address": "Большая Никитская ул., 12",
            "rating": 4.91,
            "cuisine": "Русская печь & Необистро в полумраке",
            "average_check": 4200,
            "club_perk": "Приглушенное свечное освещение, уединенная ниша для интимного неспешного диалога и комплимент от пекаря.",
            "is_active": True
        },
        {
            "name": "Harvest",
            "city": "Санкт-Петербург",
            "address": "пр. Добролюбова, 11",
            "rating": 4.95,
            "cuisine": "Zero-Waste авторская кухня Дмитрия Блинова",
            "average_check": 4500,
            "club_perk": "Лучший столик на втором уровне ресторана + фирменный десертный пейринг для резидентов «Резонанса».",
            "is_active": True
        }
    ]

    saved_venues = []
    for v in venues:
        venue_obj = Venue(**v)
        session.add(venue_obj)
        session.flush()
        saved_venues.append(venue_obj)

    print("Seeding weekly matches & date bookings...")
    # Alexander + Anna match (94% resonance)
    match1 = WeeklyMatch(
        user1_id=saved_users["Александр Волков"].id,
        user2_id=saved_users["Анна Соколова"].id,
        match_date=now.date(),
        resonance_score=94,
        status="booked",
        expires_at=now + timedelta(hours=18)
    )
    session.add(match1)
    session.flush()

    booking1 = DateBooking(
        match_id=match1.id,
        venue_id=saved_venues[0].id,  # Белуга
        booking_time=now + timedelta(days=2, hours=4),
        guests_count=2,
        status="confirmed",
        deposit_amount=5000
    )
    session.add(booking1)

    # Maxim + Sofia match (91% resonance)
    match2 = WeeklyMatch(
        user1_id=saved_users["Максим Белов"].id,
        user2_id=saved_users["София Мельникова"].id,
        match_date=now.date(),
        resonance_score=91,
        status="active_24h",
        expires_at=now + timedelta(hours=14)
    )
    session.add(match2)

    session.commit()
    session.close()
    print("Database seeding completed successfully!")


if __name__ == "__main__":
    seed_database()
