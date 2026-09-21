import os
import requests
from typing import Dict, Any, List, Optional
from backend.config import Config

class LiveSMSService:
    """
    Live Emergency SMS Notification Service.
    Sends real SMS text alerts via Twilio REST API when credentials are provided.
    Falls back gracefully to simulated in-app alerts if credentials are not configured.
    """

    @staticmethod
    def is_configured() -> bool:
        sid = Config.TWILIO_ACCOUNT_SID or os.getenv("TWILIO_ACCOUNT_SID", "")
        token = Config.TWILIO_AUTH_TOKEN or os.getenv("TWILIO_AUTH_TOKEN", "")
        phone = Config.TWILIO_PHONE_NUMBER or os.getenv("TWILIO_PHONE_NUMBER", "")
        return bool(sid and token and phone and not sid.startswith("your_"))

    @staticmethod
    def send_emergency_alert(
        to_phone: str,
        user_name: str,
        latitude: float,
        longitude: float,
        destination: str,
        nearest_haven_name: str
    ) -> Dict[str, Any]:
        map_link = f"https://maps.google.com/?q={latitude},{longitude}"
        message_body = (
            f"🚨 SafeRoute SOS Alert from {user_name}:\n"
            f"I may be in danger during my trip to '{destination}'.\n"
            f"Live GPS: {latitude:.5f}, {longitude:.5f}\n"
            f"Nearest Safe Haven: {nearest_haven_name}\n"
            f"Map Location: {map_link}"
        )

        if not LiveSMSService.is_configured():
            return {
                "success": True,
                "mode": "SIMULATED (No Twilio Key)",
                "to": to_phone,
                "message": message_body
            }

        sid = Config.TWILIO_ACCOUNT_SID or os.getenv("TWILIO_ACCOUNT_SID")
        token = Config.TWILIO_AUTH_TOKEN or os.getenv("TWILIO_AUTH_TOKEN")
        from_phone = Config.TWILIO_PHONE_NUMBER or os.getenv("TWILIO_PHONE_NUMBER")

        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        auth = (sid, token)
        data = {
            "From": from_phone,
            "To": to_phone,
            "Body": message_body
        }

        try:
            resp = requests.post(url, auth=auth, data=data, timeout=5)
            if resp.status_code in (200, 201):
                return {
                    "success": True,
                    "mode": "LIVE_SMS_DELIVERED (Twilio)",
                    "sid": resp.json().get("sid"),
                    "to": to_phone,
                    "message": message_body
                }
            else:
                return {
                    "success": False,
                    "mode": "TWILIO_ERROR",
                    "error": resp.text,
                    "to": to_phone,
                    "message": message_body
                }
        except Exception as e:
            return {
                "success": False,
                "mode": "NETWORK_ERROR",
                "error": str(e),
                "message": message_body
            }
