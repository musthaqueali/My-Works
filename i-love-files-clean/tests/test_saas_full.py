import os
import io
import sys
import unittest
from fastapi.testclient import TestClient

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
import database

class TestSaaSFull(unittest.TestCase):
    shared_email = None

    def setUp(self):
        import uuid
        self.client = TestClient(app)
        if not TestSaaSFull.shared_email:
            TestSaaSFull.shared_email = f"saas_tester_{uuid.uuid4().hex[:8]}@example.com"
        self.test_email = TestSaaSFull.shared_email
        self.test_password = "SecurePassword123!"

    def test_01_index_html_contains_saas_elements(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.text
        self.assertIn("modal-auth", html)
        self.assertIn("modal-pricing", html)
        self.assertIn("modal-quota-limit", html)
        self.assertIn("modal-api-key", html)
        self.assertIn("auth-logged-out", html)
        self.assertIn("auth-logged-in", html)
        print("[PASS] Index HTML contains all SaaS modals and auth navigation controls.")

    def test_02_auth_lifecycle(self):
        # 1. Sign up
        res = self.client.post("/api/auth/signup", json={
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Test Architect"
        })
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        user = data.get("user")
        self.assertEqual(user["email"], self.test_email)
        self.assertEqual(user["tier"], "free")
        self.assertTrue(user["api_key"].startswith("ilf_"))
        self.assertIn("ilf_session", res.cookies)
        print("[PASS] Sign up successful with signed HttpOnly session cookie.")

        # 2. Get current user
        res_me = self.client.get("/api/auth/me", cookies=res.cookies)
        self.assertEqual(res_me.status_code, 200)
        self.assertEqual(res_me.json()["user"]["email"], self.test_email)
        print("[PASS] GET /api/auth/me successfully validated cookie session.")

        # 3. Bad Sign in
        res_bad = self.client.post("/api/auth/signin", json={
            "email": self.test_email,
            "password": "WrongPassword999!"
        })
        self.assertEqual(res_bad.status_code, 401)
        print("[PASS] Bad password rejected with 401 Unauthorized.")

        # 4. Correct Sign in
        res_good = self.client.post("/api/auth/signin", json={
            "email": self.test_email,
            "password": self.test_password
        })
        self.assertEqual(res_good.status_code, 200)
        self.assertIn("ilf_session", res_good.cookies)
        print("[PASS] Correct Sign in succeeded with refreshed cookie.")

        # 5. Sign out
        res_out = self.client.post("/api/auth/signout")
        self.assertEqual(res_out.status_code, 200)
        print("[PASS] Sign out cleared session.")

    def test_03_quota_enforcement_and_pro_upgrade(self):
        # Sign in as test user
        res_auth = self.client.post("/api/auth/signin", json={
            "email": self.test_email,
            "password": self.test_password
        })
        cookies = res_auth.cookies

        # Perform free conversions up to the daily limit (5)
        user = database.get_user_by_email(self.test_email)
        used_initial = user["daily_usage_count"]
        remaining = 5 - used_initial

        for i in range(remaining):
            res_conv = self.client.post(
                "/api/convert",
                files={"file": ("test.txt", io.BytesIO(f"Test content {i}".encode("utf-8")), "text/plain")},
                data={"target_format": "pdf"},
                cookies=cookies
            )
            self.assertEqual(res_conv.status_code, 200, res_conv.text)
            conv_data = res_conv.json()
            self.assertIn("quota", conv_data)

        print(f"[PASS] Completed {remaining} free conversions up to the daily limit (5/5).")

        # Next conversion must return HTTP 429 Too Many Requests
        res_limited = self.client.post(
            "/api/convert",
            files={"file": ("test.txt", io.BytesIO(b"Blocked request"), "text/plain")},
            data={"target_format": "pdf"},
            cookies=cookies
        )
        self.assertEqual(res_limited.status_code, 429)
        self.assertIn("limit", res_limited.json()["detail"].lower())
        print("[PASS] Daily limit accurately triggered HTTP 429 for Free tier.")

        # Create Cashfree checkout order session and verify payment
        res_checkout = self.client.post(
            "/api/billing/create-checkout-session",
            json={"tier": "pro", "interval": "month"},
            cookies=cookies
        )
        self.assertEqual(res_checkout.status_code, 200)
        checkout_data = res_checkout.json()
        order_id = checkout_data.get("order_id")

        # Verify payment
        res_verify = self.client.get(f"/api/billing/verify-payment?order_id={order_id}", cookies=cookies)
        self.assertEqual(res_verify.status_code, 200)
        self.assertEqual(res_verify.json().get("tier"), "pro")
        print("[PASS] Successfully upgraded user to Pro tier via Cashfree order verification.")

        # Verify conversion now succeeds with unlimited quota
        res_pro_conv = self.client.post(
            "/api/convert",
            files={"file": ("test.txt", io.BytesIO(b"Unlimited pro conversion"), "text/plain")},
            data={"target_format": "pdf"},
            cookies=cookies
        )
        self.assertEqual(res_pro_conv.status_code, 200)
        pro_quota = res_pro_conv.json()["quota"]
        self.assertEqual(pro_quota["tier"], "pro")
        self.assertIn(pro_quota["limit"], (-1, "Unlimited"))
        print("[PASS] Pro user enjoys unlimited conversions with zero quota blocking!")

    def test_04_api_key_authentication(self):
        user = database.get_user_by_email(self.test_email)
        api_key = user["api_key"]

        # Convert using X-API-Key header (no cookies)
        res_api = self.client.post(
            "/api/convert",
            files={"file": ("api_test.txt", io.BytesIO(b"API key test"), "text/plain")},
            data={"target_format": "pdf"},
            headers={"X-API-Key": api_key}
        )
        self.assertEqual(res_api.status_code, 200, res_api.text)
        self.assertEqual(res_api.json()["quota"]["tier"], "pro")
        print("[PASS] X-API-Key header successfully authenticated request without cookies.")

    def test_05_guest_quota_enforcement(self):
        import random
        # Create a fresh TestClient to use a distinct guest IP simulation
        client = TestClient(app)
        guest_headers = {"X-Forwarded-For": f"203.0.113.{random.randint(10, 240)}"}

        # Guest gets 3 conversions
        for i in range(3):
            res = client.post(
                "/api/convert",
                files={"file": (f"guest_{i}.txt", io.BytesIO(b"Guest conversion text"), "text/plain")},
                data={"target_format": "pdf"},
                headers=guest_headers
            )
            self.assertEqual(res.status_code, 200, res.text)
            self.assertEqual(res.json()["quota"]["tier"], "guest")
        print("[PASS] Guest visitor successfully performed 3 conversions.")

        # 4th conversion must fail with 429
        res_blocked = client.post(
            "/api/convert",
            files={"file": ("guest_blocked.txt", io.BytesIO(b"Guest conversion text"), "text/plain")},
            data={"target_format": "pdf"},
            headers=guest_headers
        )
        self.assertEqual(res_blocked.status_code, 429)
        self.assertIn("limit", res_blocked.json()["detail"].lower())
        print("[PASS] Guest visitor 4th conversion accurately blocked with HTTP 429 limit.")

if __name__ == "__main__":
    unittest.main()

