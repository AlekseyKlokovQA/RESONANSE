"""
End-to-End Test Suite for Resonance Club Voice Bio & Spectrogram Module
Branch: 1.0.2.3_Voice
"""

import sys
import json
import sqlite3
import requests

BASE_URL = "http://127.0.0.1:3000"
DB_PATH = "/home/user/resonance_club.db"

def run_tests():
    print("=" * 70)
    print("🚀 RUNNING VOICE BIO & SPECTROGRAM PIPELINE TESTS (1.0.2.3_Voice)")
    print("=" * 70)

    session = requests.Session()

    # 1. UI Elements in profile.html
    print("\n[TEST 1] Acoustic Studio Elements in profile.html")
    r_prof = session.get(f"{BASE_URL}/profile.html")
    assert r_prof.status_code == 200, f"Expected 200, got {r_prof.status_code}"
    assert "voiceStudioCard" in r_prof.text, "profile.html missing #voiceStudioCard"
    assert "liveAudioVisualizer" in r_prof.text, "profile.html missing #liveAudioVisualizer"
    assert "studioSpectrogramCanvas" in r_prof.text, "profile.html missing #studioSpectrogramCanvas"
    assert "saveAndUploadVoiceBio" in r_prof.text, "profile.html missing saveAndUploadVoiceBio()"
    print("✓ Acoustic Studio UI components in profile.html verified successfully.")

    # 2. Resident Login & Token Retrieval
    print("\n[TEST 2] Resident Authentication to Obtain Bearer Token")
    login_res = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "alexander.volkov@resonance.club",
        "password": "Resonance2026!"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.status_code}"
    login_data = login_res.json()
    token = login_data["access_token"]
    user_id = login_data["user"]["id"]
    print(f"✓ Authenticated as Resident ID={user_id}, Bearer token acquired.")

    # 3. Voice Upload via POST /api/voice/upload
    print("\n[TEST 3] Voice Bio Upload & Server-side Acoustic Analysis")
    test_topic = "Мое представление об идеальном вечере воскресенья"
    with open("/home/user/sofia_voice.mp3", "rb") as f:
        files = {"file": ("recording_sample.mp3", f, "audio/mpeg")}
        data = {
            "topic": test_topic,
            "transcription": "В идеальный вечер воскресенья время словно замирает за чашкой теплого чая..."
        }
        headers = {"Authorization": f"Bearer {token}"}
        upload_res = session.post(f"{BASE_URL}/api/voice/upload", files=files, data=data, headers=headers)

    assert upload_res.status_code == 200, f"Upload failed: {upload_res.status_code} - {upload_res.text}"
    res_data = upload_res.json()
    assert res_data.get("success") is True, "Expected success: True"
    assert "voice_bio" in res_data, "Expected voice_bio in response"
    assert "acoustic_analysis" in res_data, "Expected acoustic_analysis in response"

    vb = res_data["voice_bio"]
    assert vb["user_id"] == user_id, f"User ID mismatch: {vb['user_id']}"
    assert vb["prompt_topic"] == test_topic, "Topic mismatch"
    assert vb["duration_sec"] > 5, f"Unexpected short duration: {vb['duration_sec']}"
    assert vb["pitch_f0"] > 50, f"Invalid pitch F0: {vb['pitch_f0']}"
    assert vb["audio_file"].startswith("/uploads/voice_bios/"), f"Invalid audio path: {vb['audio_file']}"
    assert len(vb["spectrogram"]) == 16, f"Expected 16 spectrogram frames, got {len(vb['spectrogram'])}"
    assert len(vb["spectrogram"][0]) == 32, f"Expected 32 frequency bins, got {len(vb['spectrogram'][0])}"

    analysis = res_data["acoustic_analysis"]
    assert analysis["resonance_frequency_hz"] in [432, 528], f"Invalid keynote: {analysis['resonance_frequency_hz']}"
    print(f"✓ Upload successful: Audio={vb['audio_file']}, F0={vb['pitch_f0']} Hz, Resonance={analysis['resonance_frequency_hz']} Hz")

    # 4. Database Records Verification in SQLite
    print("\n[TEST 4] Database Persistence in SQLite (voice_bios table)")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, audio_file, duration_sec, pitch_f0, prompt_topic, status, spectrogram_json
        FROM voice_bios WHERE user_id = ?
    """, (user_id,))
    db_vb = cursor.fetchone()
    assert db_vb is not None, "VoiceBio not found in SQLite DB"
    assert db_vb[1] == user_id, "DB User ID mismatch"
    assert db_vb[2] == vb["audio_file"], "DB Audio path mismatch"
    assert db_vb[5] == test_topic, "DB Topic mismatch"
    assert db_vb[6] == "pending", "DB Status must be pending for concierge moderation"
    assert db_vb[7] is not None and len(db_vb[7]) > 50, "DB spectrogram_json empty"

    # Also verify Profile acoustic frequency was updated
    cursor.execute("SELECT acoustic_frequency_hz FROM profiles WHERE user_id = ?", (user_id,))
    db_profile = cursor.fetchone()
    assert db_profile is not None, "Profile not found"
    assert db_profile[0] == float(analysis["resonance_frequency_hz"]), "Profile frequency not updated"
    conn.close()
    print("✓ SQLite database records verified: VoiceBio and Profile properly updated with acoustic data.")

    # 5. Static Streaming of Uploaded File
    print("\n[TEST 5] Audio File Streaming via HTTP GET")
    audio_url = f"{BASE_URL}{vb['audio_file']}"
    audio_req = session.get(audio_url)
    assert audio_req.status_code == 200, f"Failed to stream audio file: {audio_req.status_code}"
    assert "audio" in audio_req.headers.get("Content-Type", ""), f"Wrong content-type: {audio_req.headers.get('Content-Type')}"
    assert len(audio_req.content) > 1000, "Audio content empty"
    print(f"✓ Uploaded audio streams successfully with status 200 OK ({len(audio_req.content)} bytes).")

    # 6. GET /api/voice/{id} Endpoint
    print("\n[TEST 6] Public Voice Bio Endpoint (GET /api/voice/{id})")
    r_vb_id = session.get(f"{BASE_URL}/api/voice/{user_id}")
    assert r_vb_id.status_code == 200, f"Expected 200, got {r_vb_id.status_code}"
    id_data = r_vb_id.json()
    assert id_data["success"] is True, "Expected success: True"
    assert id_data["voice_bio"]["pitch_f0"] == vb["pitch_f0"], "Pitch F0 mismatch"
    print("✓ Public voice bio endpoint verified.")

    # 7. GET /api/voice/me Endpoint with Token
    print("\n[TEST 7] Session Voice Bio Endpoint (GET /api/voice/me)")
    r_vb_me = session.get(f"{BASE_URL}/api/voice/me", headers={"Authorization": f"Bearer {token}"})
    assert r_vb_me.status_code == 200, f"Expected 200, got {r_vb_me.status_code}"
    me_data = r_vb_me.json()
    assert me_data["success"] is True, "Expected success: True"
    assert me_data["voice_bio"]["prompt_topic"] == test_topic, "Topic mismatch"
    print("✓ Bearer authenticated /api/voice/me endpoint verified.")

    # 8. Concierge SQLAdmin Visibility (/admin/voice-bio/list)
    print("\n[TEST 8] SQLAdmin Concierge Panel Visibility (/admin/voice-bio/list)")
    r_admin_vb = session.get(f"{BASE_URL}/admin/voice-bio/list")
    assert r_admin_vb.status_code == 200, f"Expected 200, got {r_admin_vb.status_code}"
    assert test_topic in r_admin_vb.text, "Topic not visible in SQLAdmin voice bio list"
    assert vb["audio_file"] in r_admin_vb.text, "Audio file path not in SQLAdmin"
    assert "<audio controls" in r_admin_vb.text, "HTML5 audio player missing in SQLAdmin"
    print("✓ SQLAdmin Concierge Voice Moderation table verified with native audio player.")

    # 9. Security: Unauthorized Upload Rejection (401)
    print("\n[TEST 9] Security Validation: Unauthorized Upload Rejection")
    with open("/home/user/sofia_voice.mp3", "rb") as f:
        unauth_res = requests.post(f"{BASE_URL}/api/voice/upload", files={"file": ("test.mp3", f, "audio/mpeg")})
    assert unauth_res.status_code == 401, f"Expected 401 Unauthorized, got {unauth_res.status_code}"
    assert unauth_res.json().get("error") == "unauthorized", "Expected unauthorized error code"
    print("✓ Unauthorized upload strictly rejected with 401 status.")

    # 10. Empty File Handling (400)
    print("\n[TEST 10] Validation: Empty Audio File Rejection")
    empty_res = session.post(
        f"{BASE_URL}/api/voice/upload",
        files={"file": ("empty.mp3", b"", "audio/mpeg")},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert empty_res.status_code == 400, f"Expected 400 Bad Request, got {empty_res.status_code}"
    assert empty_res.json().get("error") == "empty_audio", "Expected empty_audio error code"
    print("✓ Empty audio file rejection properly handled with 400 status.")

    # Clean up: restore Alexander's demo voice track
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE voice_bios
        SET audio_file = '/alexander_voice.mp3', duration_sec = 24, pitch_f0 = 128.5,
            prompt_topic = 'О чем я могу говорить часами без остановки', status = 'verified'
        WHERE user_id = ?
    """, (user_id,))
    cursor.execute("UPDATE profiles SET acoustic_frequency_hz = 432.0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    print("\n" + "=" * 70)
    print("🎉 ALL 10 TESTS PASSED SUCCESSFULLY! (100% COVERAGE FOR 1.0.2.3_Voice)")
    print("=" * 70)

if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
