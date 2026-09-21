import unittest
import json
from backend.app import create_app
from backend.database.db import db
from backend.models.models import User

class TestAuth(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_registration_and_login_flow(self):
        # 1. Register a new user
        reg_payload = {
            "full_name": "Taylor Swift",
            "email": "taylor@saferoute.app",
            "password": "SecurePassword123!",
            "phone": "+15551234567",
            "emergency_contact_name": "Andrea Swift",
            "emergency_contact_phone": "+15557654321"
        }
        res = self.client.post(
            "/api/auth/register",
            data=json.dumps(reg_payload),
            content_type="application/json"
        )
        self.assertIn(res.status_code, [201, 409]) # 201 created or 409 if already registered in db

        # 2. Login
        login_payload = {
            "email": "taylor@saferoute.app",
            "password": "SecurePassword123!"
        }
        login_res = self.client.post(
            "/api/auth/login",
            data=json.dumps(login_payload),
            content_type="application/json"
        )
        self.assertEqual(login_res.status_code, 200)
        data = json.loads(login_res.data)
        self.assertIn("token", data)
        self.assertEqual(data["user"]["email"], "taylor@saferoute.app")

    def test_invalid_login_credentials(self):
        login_payload = {
            "email": "nonexistent@saferoute.app",
            "password": "wrongpassword"
        }
        res = self.client.post(
            "/api/auth/login",
            data=json.dumps(login_payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 401)

if __name__ == "__main__":
    unittest.main()
