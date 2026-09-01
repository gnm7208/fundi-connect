"""Safaricom Daraja M-PESA integration and sandbox simulator."""

import base64
import uuid
from datetime import UTC, datetime

import requests
from flask import current_app

from server.utils.formatters import normalize_phone_number


class DarajaService:
    """Service for interacting with Safaricom Daraja M-PESA API."""

    def __init__(self):
        self.env = current_app.config.get("DARAJA_ENVIRONMENT", "sandbox")
        self.consumer_key = current_app.config.get("DARAJA_CONSUMER_KEY")
        self.consumer_secret = current_app.config.get("DARAJA_CONSUMER_SECRET")
        self.passkey = current_app.config.get("DARAJA_PASSKEY")
        self.shortcode = current_app.config.get("DARAJA_SHORTCODE", "174379")
        self.callback_url = current_app.config.get("DARAJA_CALLBACK_URL")
        self.simulation_mode = current_app.config.get("DARAJA_SIMULATION_MODE", True)

        self.base_url = (
            "https://sandbox.safaricom.co.ke"
            if self.env == "sandbox"
            else "https://api.safaricom.co.ke"
        )

    def generate_access_token(self) -> str:
        """Obtain OAuth access token from Safaricom Daraja."""
        if self.simulation_mode:
            return "simulated_daraja_access_token"

        auth_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        auth_string = f"{self.consumer_key}:{self.consumer_secret}"
        encoded_auth = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

        headers = {"Authorization": f"Basic {encoded_auth}"}
        response = requests.get(auth_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("access_token")
        raise RuntimeError(f"Daraja OAuth failed: {response.text}")

    def generate_password(self, timestamp: str) -> str:
        """Generate Daraja Lipa Na M-Pesa password."""
        raw_password = f"{self.shortcode}{self.passkey}{timestamp}"
        return base64.b64encode(raw_password.encode("utf-8")).decode("utf-8")

    def initiate_stk_push(
        self,
        phone_number: str,
        amount_cents: int,
        booking_id: str,
        description: str = "Fundi Connect Escrow Deposit",
    ) -> dict:
        """Initiate STK Push (Lipa Na M-PESA Online).

        amount_cents is in minor units (e.g. 150000 = KES 1500).
        Daraja accepts whole Kenyan shillings.
        """
        normalized_phone = normalize_phone_number(phone_number)
        amount_kes = max(1, amount_cents // 100)

        # If simulation mode is active (for dev/test or mock demo):
        if self.simulation_mode:
            simulated_checkout_id = (
                f"ws_CO_{datetime.now(UTC).strftime('%d%m%Y%H%M%S')}_{uuid.uuid4().hex[:8]}"
            )
            return {
                "success": True,
                "simulation": True,
                "MerchantRequestID": f"MR_{uuid.uuid4().hex[:10]}",
                "CheckoutRequestID": simulated_checkout_id,
                "ResponseCode": "0",
                "ResponseDescription": "Success. Request accepted for processing (Simulated)",
                "CustomerMessage": f"Simulated STK Push sent to {normalized_phone} for KES {amount_kes}",
            }

        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        password = self.generate_password(timestamp)
        token = self.generate_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount_kes,
            "PartyA": normalized_phone,
            "PartyB": self.shortcode,
            "PhoneNumber": normalized_phone,
            "CallBackURL": self.callback_url,
            "AccountReference": f"FC-{booking_id[:8].upper()}",
            "TransactionDesc": description[:128],
        }

        response = requests.post(
            f"{self.base_url}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers=headers,
            timeout=15,
        )

        result = response.json()
        result["success"] = response.status_code == 200 and result.get("ResponseCode") == "0"
        return result

    def initiate_b2c_payout(
        self,
        phone_number: str,
        amount_cents: int,
        transaction_id: str,
        remarks: str = "Fundi Connect Earnings Payout",
    ) -> dict:
        """Send earnings payout from business to Fundi M-PESA phone number."""
        normalized_phone = normalize_phone_number(phone_number)
        amount_kes = max(1, amount_cents // 100)

        if self.simulation_mode:
            receipt = (
                f"FC_B2C_{datetime.now(UTC).strftime('%Y%m%d')}_{uuid.uuid4().hex[:6].upper()}"
            )
            return {
                "success": True,
                "simulation": True,
                "ReceiptNumber": receipt,
                "ConversationID": f"AG_{uuid.uuid4().hex[:8]}",
                "ResponseCode": "0",
                "ResponseDescription": f"Simulated B2C payout of KES {amount_kes} sent to {normalized_phone}",
            }

        # Live B2C implementation
        token = self.generate_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "InitiatorName": current_app.config.get("DARAJA_INITIATOR_NAME", "fundi_admin"),
            "SecurityCredential": current_app.config.get("DARAJA_SECURITY_CREDENTIAL", ""),
            "CommandID": "BusinessPayment",
            "Amount": amount_kes,
            "PartyA": self.shortcode,
            "PartyB": normalized_phone,
            "Remarks": remarks,
            "QueueTimeOutURL": current_app.config.get("DARAJA_TIMEOUT_URL", self.callback_url),
            "ResultURL": current_app.config.get("DARAJA_B2C_RESULT_URL", self.callback_url),
            "Occasion": f"FC-{transaction_id[:8]}",
        }

        response = requests.post(
            f"{self.base_url}/mpesa/b2c/v1/paymentrequest",
            json=payload,
            headers=headers,
            timeout=15,
        )
        result = response.json()
        result["success"] = response.status_code == 200 and result.get("ResponseCode") == "0"
        return result
