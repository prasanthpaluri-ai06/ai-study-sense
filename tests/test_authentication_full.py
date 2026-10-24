import base64
import json
import cv2
import numpy as np
import pytest
from httpx import AsyncClient


def create_synthetic_face_base64(variation: bool = False, imposter: bool = False) -> str:
    """Creates a synthetic face JPEG in base64 format for end-to-end vision testing."""
    img = np.ones((240, 240, 3), dtype=np.uint8) * 160
    
    if not imposter:
        # Subject A: Eyes at row 70, nose at center, mouth at row 160
        img[65:85, 50:80] = 30
        img[65:85, 160:190] = 30
        img[100:135, 115:125] = 50
        img[160:185, 80:160] = 40
        if variation:
            # Slight head movement / lighting variation
            img = np.roll(img, shift=(2, -2), axis=(0, 1))
            img = np.clip(img.astype(np.float32) * 1.1 + np.random.normal(0, 3, img.shape), 0, 255).astype(np.uint8)
    else:
        # Subject B: Imposter with different spatial landmarks
        img[90:110, 35:75] = 20
        img[90:110, 165:205] = 20
        img[115:150, 100:140] = 40
        img[180:200, 100:140] = 30

    _, buffer = cv2.imencode(".jpg", img)
    return "data:image/jpeg;base64," + base64.b64encode(buffer).decode("utf-8")


@pytest.mark.asyncio
async def test_full_authentication_lifecycle(client: AsyncClient):
    face_a = create_synthetic_face_base64(variation=False, imposter=False)
    face_a_var = create_synthetic_face_base64(variation=True, imposter=False)
    face_imposter = create_synthetic_face_base64(variation=False, imposter=True)

    # ----------------------------------------------------
    # TEST 1: Face Frame Validation Endpoint
    # ----------------------------------------------------
    val_res = await client.post("/api/v1/auth/face/validate", json={"face_image_base64": face_a})
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["valid"] is True
    assert val_data["has_embedding"] is True

    # Dark / invalid frame rejection
    dark_img = np.zeros((200, 200, 3), dtype=np.uint8)
    _, dark_buf = cv2.imencode(".jpg", dark_img)
    dark_b64 = "data:image/jpeg;base64," + base64.b64encode(dark_buf).decode("utf-8")
    val_dark = await client.post("/api/v1/auth/face/validate", json={"face_image_base64": dark_b64})
    assert val_dark.status_code == 200
    assert val_dark.json()["valid"] is False
    assert "low" in val_dark.json()["message"].lower()

    # ----------------------------------------------------
    # TEST 2: Simplified Registration (No Course, Year, Semester) with Face Registration
    # ----------------------------------------------------
    register_payload = {
        "full_name": "Marcus Aurelius",
        "username": "marcus_a",
        "email": "marcus@academy.edu",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "institution": "Royal Institute of Tech",
        "face_image_base64": face_a,
    }

    reg_res = await client.post("/api/v1/auth/register", json=register_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["username"] == "marcus_a"

    # ----------------------------------------------------
    # TEST 3: Duplicate User ID Rejection
    # ----------------------------------------------------
    dup_res = await client.post("/api/v1/auth/register", json=register_payload)
    assert dup_res.status_code == 400
    assert "already taken" in dup_res.json()["detail"].lower()

    # ----------------------------------------------------
    # TEST 4: Step 1 Login - Wrong Password Rejection
    # ----------------------------------------------------
    wrong_pwd_res = await client.post(
        "/api/v1/auth/verify-credentials",
        json={"username": "marcus_a", "password": "WrongPassword999!"},
    )
    assert wrong_pwd_res.status_code == 401
    assert "invalid" in wrong_pwd_res.json()["detail"].lower()

    # ----------------------------------------------------
    # TEST 5: Step 1 Login - Correct Password Verification
    # ----------------------------------------------------
    verify_res = await client.post(
        "/api/v1/auth/verify-credentials",
        json={"username": "marcus_a", "password": "SecurePassword123!"},
    )
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["status"] == "verified"
    assert verify_data["has_face_enrolled"] is True
    assert "session_challenge" in verify_data
    challenge = verify_data["session_challenge"]

    # ----------------------------------------------------
    # TEST 6: Step 2 Login - Wrong Face (Imposter Mismatch Rejection)
    # ----------------------------------------------------
    wrong_face_res = await client.post(
        "/api/v1/auth/face/login",
        json={
            "username": "marcus_a",
            "session_challenge": challenge,
            "face_image_base64": face_imposter,
        },
    )
    assert wrong_face_res.status_code == 401
    assert "failed" in wrong_face_res.json()["detail"].lower()

    # ----------------------------------------------------
    # TEST 7: Step 2 Login - Correct Face with Lighting Variation (Success)
    # ----------------------------------------------------
    correct_face_res = await client.post(
        "/api/v1/auth/face/login",
        json={
            "username": "marcus_a",
            "session_challenge": challenge,
            "face_image_base64": face_a_var,
        },
    )
    assert correct_face_res.status_code == 200
    login_data = correct_face_res.json()
    assert "access_token" in login_data
    auth_token = login_data["access_token"]

    # ----------------------------------------------------
    # TEST 8: Protected Route Access with Valid Token
    # ----------------------------------------------------
    headers = {"Authorization": f"Bearer {auth_token}"}
    me_res = await client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["username"] == "marcus_a"
    assert me_data["profile"]["institution"] == "Royal Institute of Tech"
    assert me_data["has_face_enrolled"] is True

    # ----------------------------------------------------
    # TEST 9: Protected Route Access Without / With Invalid Token
    # ----------------------------------------------------
    no_auth_res = await client.get("/api/v1/users/me")
    assert no_auth_res.status_code == 401

    bad_token_res = await client.get("/api/v1/users/me", headers={"Authorization": "Bearer invalid_garbage_token"})
    assert bad_token_res.status_code == 401

    # ----------------------------------------------------
    # TEST 10: Secure Password Fallback Login
    # ----------------------------------------------------
    fallback_res = await client.post(
        "/api/v1/auth/fallback-login",
        json={
            "username": "marcus_a",
            "password": "SecurePassword123!",
            "reason": "Webcam lighting degraded",
        },
    )
    assert fallback_res.status_code == 200
    fallback_data = fallback_res.json()
    assert "access_token" in fallback_data

    # ----------------------------------------------------
    # TEST 11: Logout Event
    # ----------------------------------------------------
    logout_res = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "logged_out"
