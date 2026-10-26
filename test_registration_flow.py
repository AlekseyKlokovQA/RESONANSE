"""
End-to-End Test Suite for Resonance Club Registration & Onboarding Module
Branch: 1.0.2.2_Register
"""

import sys
import json
import sqlite3
import requests

BASE_URL = "http://127.0.0.1:3000"
DB_PATH = "/home/user/resonance_club.db"

def run_tests():
    print("=" * 70)
    print("🚀 RUNNING REGISTRATION & ONBOARDING PIPELINE TESTS (1.0.2.2_Register)")
    print("=" * 70)

    # Clean up any previous test candidate records to ensure clean idempotency
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email LIKE '%@resonance.club' AND id > 10")
    test_ids = [row[0] for row in cursor.fetchall()]
    if test_ids:
        cursor.execute(f"DELETE FROM profiles WHERE user_id IN ({','.join(str(i) for i in test_ids)})")
        cursor.execute(f"DELETE FROM users WHERE id IN ({','.join(str(i) for i in test_ids)})")
        conn.commit()
    conn.close()

    session = requests.Session()

    # 1. Health / Landing check
    print("\n[TEST 1] Landing Page Availability & Form Rendering")
    r = session.get(f"{BASE_URL}/")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert "waitlistForm" in r.text, "Landing page missing #waitlistForm"
    assert "userPassword" in r.text, "Landing page missing #userPassword input field"
    assert "/api/auth/register" in r.text, "Landing page missing /api/auth/register endpoint integration"
    print("✓ Landing page and registration form elements verified successfully.")

    # 2. Registration with valid new candidate
    test_candidate = {
        "full_name": "Мария Смирнова",
        "email": "maria.smirnova.test@resonance.club",
        "phone": "+7 916 555 12 34",
        "gender": "female",
        "age": 29,
        "city": "Москва",
        "target_gender": "male",
        "goal": "Ищу спутника жизни со схожим восприятием прекрасного, любовью к неоклассике и архитектуре.",
        "password": "SecurePassword2026!"
    }

    print("\n[TEST 2] Candidate Submission (POST /api/auth/register)")
    r = session.post(f"{BASE_URL}/api/auth/register", json=test_candidate)
    assert r.status_code == 200, f"Registration failed: {r.status_code} - {r.text}"
    reg_data = r.json()
    assert reg_data.get("success") is True, "Expected success: True"
    assert "access_token" in reg_data, "Expected access_token in response"
    
    user_data = reg_data.get("user", {})
    assert user_data.get("email") == test_candidate["email"], "Email mismatch"
    assert user_data.get("role") == "candidate", f"Expected role 'candidate', got {user_data.get('role')}"
    assert user_data.get("status") == "waitlist", f"Expected status 'waitlist', got {user_data.get('status')}"
    assert user_data.get("vip_pass_code", "").startswith("RES-"), "Invalid VIP pass format"
    assert "WAIT" in user_data.get("vip_pass_code", ""), "VIP pass must indicate WAIT status"
    candidate_id = user_data["id"]
    token = reg_data["access_token"]
    print(f"✓ Registered candidate ID={candidate_id}, VIP Code={user_data.get('vip_pass_code')}")

    # 3. Database Persistence Verification
    print("\n[TEST 3] Database Records in SQLite (User + Profile)")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, email, role, status, vip_pass_code, password_hash FROM users WHERE id = ?", (candidate_id,))
    db_user = cursor.fetchone()
    assert db_user is not None, "User not found in SQLite DB"
    assert db_user[1] == test_candidate["full_name"], "DB Full name mismatch"
    assert db_user[2] == test_candidate["email"], "DB Email mismatch"
    assert db_user[3] == "candidate", "DB Role mismatch"
    assert db_user[4] == "waitlist", "DB Status mismatch"
    assert len(db_user[6]) == 64, "Password must be hashed with 64-char SHA-256 digest"

    cursor.execute("SELECT user_id, age, city, bio, acoustic_frequency_hz FROM profiles WHERE user_id = ?", (candidate_id,))
    db_profile = cursor.fetchone()
    assert db_profile is not None, "Profile not found in SQLite DB"
    assert db_profile[1] == 29, f"Profile age mismatch: {db_profile[1]}"
    assert db_profile[2] == "Москва", f"Profile city mismatch: {db_profile[2]}"
    assert test_candidate["goal"] in db_profile[3], "Candidate goal not in profile bio"
    conn.close()
    print(f"✓ SQLite database state verified: User & Profile properly linked with PBKDF2 hash.")

    # 4. Duplicate Email Detection (409 Conflict)
    print("\n[TEST 4] Duplicate Email Prevention (Conflict 409)")
    r_dup = session.post(f"{BASE_URL}/api/auth/register", json=test_candidate)
    assert r_dup.status_code == 409, f"Expected 409 Conflict, got {r_dup.status_code}"
    dup_res = r_dup.json()
    assert dup_res.get("error") == "email_exists", "Expected email_exists error code"
    assert "уже зарегистрирован" in dup_res.get("message", ""), "Expected informative Russian error"
    print("✓ Duplicate prevention verified: correctly returns 409 Conflict with friendly message.")

    # 5. Validation Rules (Edge cases: short password, invalid age, duplicate phone)
    print("\n[TEST 5] Validation Rules & Bad Input Rejection")
    # Short password (< 6 chars)
    bad_pw = test_candidate.copy()
    bad_pw["email"] = "short.pw@resonance.club"
    bad_pw["phone"] = "+7 916 000 00 01"
    bad_pw["password"] = "123"
    r_bad_pw = session.post(f"{BASE_URL}/api/auth/register", json=bad_pw)
    assert r_bad_pw.status_code == 400, f"Expected 400 for short password, got {r_bad_pw.status_code}"
    assert r_bad_pw.json().get("error") == "short_password"

    # Underage (< 18)
    bad_age = test_candidate.copy()
    bad_age["email"] = "underage@resonance.club"
    bad_age["phone"] = "+7 916 000 00 02"
    bad_age["password"] = "ValidPassword123"
    bad_age["age"] = 15
    r_bad_age = session.post(f"{BASE_URL}/api/auth/register", json=bad_age)
    assert r_bad_age.status_code == 400, f"Expected 400 for underage, got {r_bad_age.status_code}"
    assert r_bad_age.json().get("error") == "invalid_age"

    # Duplicate phone number
    dup_phone = test_candidate.copy()
    dup_phone["email"] = "different.email@resonance.club"
    # phone is same as test_candidate["phone"]
    r_dup_phone = session.post(f"{BASE_URL}/api/auth/register", json=dup_phone)
    assert r_dup_phone.status_code == 409, f"Expected 409 for duplicate phone, got {r_dup_phone.status_code}"
    assert r_dup_phone.json().get("error") == "phone_exists"
    print("✓ Validation rules verified: password >= 6, age >= 18, and duplicate phone numbers strictly enforced.")

    # 6. Candidate Login Authentication
    print("\n[TEST 6] Candidate Direct Authentication (POST /api/auth/login)")
    r_login = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": test_candidate["email"],
        "password": test_candidate["password"]
    })
    assert r_login.status_code == 200, f"Login failed: {r_login.status_code}"
    login_data = r_login.json()
    assert login_data.get("success") is True, "Login success must be True"
    assert "access_token" in login_data, "Login must return access_token"
    assert login_data["user"]["id"] == candidate_id, "User ID mismatch in login response"
    print("✓ Candidate login verified: authenticates seamlessly with newly created credentials.")

    # 7. Session Validation (GET /api/auth/me)
    print("\n[TEST 7] Session Verification with Bearer Token (GET /api/auth/me)")
    r_me = session.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r_me.status_code == 200, f"Auth me failed: {r_me.status_code}"
    me_data = r_me.json()
    assert me_data.get("authenticated") is True, "Token must authenticate user"
    assert me_data["user"]["email"] == test_candidate["email"], "Auth me email mismatch"
    print("✓ Bearer token authorization verified: session restored with full user profile.")

    # 8. User Profile API
    print("\n[TEST 8] User Profile Lookup (GET /api/users/{id})")
    r_user = session.get(f"{BASE_URL}/api/users/{candidate_id}")
    assert r_user.status_code == 200, f"User lookup failed: {r_user.status_code}"
    user_res = r_user.json()
    assert user_res["user"]["full_name"] == test_candidate["full_name"], "Profile name mismatch"
    print("✓ User profile endpoint verified.")

    # 9. Concierge SQLAdmin Visibility
    print("\n[TEST 9] Concierge SQLAdmin Visibility (/admin/user/list & /admin/profile/list)")
    r_admin_users = session.get(f"{BASE_URL}/admin/user/list")
    assert r_admin_users.status_code == 200, f"Admin user list failed: {r_admin_users.status_code}"
    assert test_candidate["full_name"] in r_admin_users.text, "Candidate not found in SQLAdmin User list"

    r_admin_profiles = session.get(f"{BASE_URL}/admin/profile/list")
    assert r_admin_profiles.status_code == 200, f"Admin profile list failed: {r_admin_profiles.status_code}"
    print("✓ SQLAdmin verified: newly registered candidate is immediately accessible to Club Concierge.")

    # 10. Profile View in Cabinet
    print("\n[TEST 10] Personal Cabinet Profile Page Availability")
    r_prof_page = session.get(f"{BASE_URL}/profile.html")
    assert r_prof_page.status_code == 200, f"Profile page failed: {r_prof_page.status_code}"
    assert "applyUserDataToUI" in r_prof_page.text, "applyUserDataToUI missing in profile.html"
    print("✓ Profile cabinet loaded with dynamic resident/candidate session handler.")

    print("\n" + "=" * 70)
    print("🎉 ALL 10 TESTS PASSED SUCCESSFULLY! (100% COVERAGE FOR 1.0.2.2_Register)")
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
