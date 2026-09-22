import os
import io
import sys
import uuid
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
import database

class TestCashfreeBilling(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_email = f"cf_tester_{uuid.uuid4().hex[:8]}@example.com"
        self.test_password = "SecurePassword123!"

    def test_01_plans_endpoint(self):
        res = self.client.get("/api/billing/plans")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["currency"], "INR")
        self.assertEqual(data["symbol"], "₹")
        self.assertEqual(data["provider"], "Cashfree Payments")
        self.assertTrue(data["is_sandbox"])
        print("[PASS] Cashfree plans returned INR pricing and Sandbox configuration.")

    def test_02_create_cashfree_order_session(self):
        # 1. Sign up user
        res_signup = self.client.post("/api/auth/signup", json={
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Cashfree Architect"
        })
        self.assertEqual(res_signup.status_code, 200)
        cookies = res_signup.cookies

        # 2. Call create-checkout-session with Cashfree Sandbox API
        res_order = self.client.post(
            "/api/billing/create-checkout-session",
            json={"tier": "pro", "interval": "month"},
            cookies=cookies
        )
        self.assertEqual(res_order.status_code, 200, res_order.text)
        data = res_order.json()
        self.assertEqual(data.get("mode"), "cashfree")
        self.assertEqual(data.get("currency"), "INR")
        self.assertEqual(data.get("environment"), "sandbox")
        self.assertIsNotNone(data.get("payment_session_id"))
        self.assertTrue(data["payment_session_id"].startswith("session_"))
        print(f"[PASS] Successfully created real Cashfree Sandbox order: {data.get('order_id')}")
        print(f"       Payment Session ID: {data.get('payment_session_id')[:35]}...")

        # 3. Verify Payment endpoint
        order_id = data.get("order_id")
        res_verify = self.client.get(
            f"/api/billing/verify-payment?order_id={order_id}",
            cookies=cookies
        )
        self.assertEqual(res_verify.status_code, 200, res_verify.text)
        verify_data = res_verify.json()
        self.assertEqual(verify_data.get("status"), "success")
        self.assertEqual(verify_data.get("tier"), "pro")
        print("[PASS] Verify payment endpoint successfully verified order and upgraded tier to PRO.")

        # 4. Check user profile reflects PRO tier
        res_me = self.client.get("/api/auth/me", cookies=cookies)
        self.assertEqual(res_me.status_code, 200)
        user_info = res_me.json()["user"]
        self.assertEqual(user_info["tier"], "pro")
        print("[PASS] User account is now officially verified as PRO tier!")

        # 5. Verify unlimited conversions work
        res_conv = self.client.post(
            "/api/convert",
            files={"file": ("pro_test.txt", io.BytesIO(b"Cashfree Pro conversion test"), "text/plain")},
            data={"target_format": "pdf"},
            cookies=cookies
        )
        self.assertEqual(res_conv.status_code, 200)
        self.assertEqual(res_conv.json()["quota"]["tier"], "pro")
        print("[PASS] Cashfree-upgraded Pro user converted file with unlimited quota.")

if __name__ == "__main__":
    unittest.main()
