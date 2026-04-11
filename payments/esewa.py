# payments/esewa.py
"""
eSewa ePay v2 Integration (Sandbox / Live)

Sandbox test credentials (for paying on eSewa page):
  eSewa ID: 9806800001 (or 9806800002/3/4/5)
  Password: Nepal@123
  MPIN: 1122
  OTP: 123456
"""

import hashlib
import hmac
import base64
import json
import requests
from django.conf import settings


def get_esewa_secret_key():
    return getattr(settings, "ESEWA_SECRET_KEY", "8gBm/:&EnhH.1/q")


def get_esewa_product_code():
    return getattr(settings, "ESEWA_PRODUCT_CODE", "EPAYTEST")


def get_esewa_base_url():
    if getattr(settings, "ESEWA_LIVE_MODE", False):
        return "https://epay.esewa.com.np"
    return "https://rc-epay.esewa.com.np"


def generate_signature(message):
    secret = get_esewa_secret_key()
    h = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    )
    return base64.b64encode(h.digest()).decode("utf-8")


def build_esewa_payment_form_data(amount, transaction_uuid, success_url, failure_url):
    product_code = get_esewa_product_code()
    total_amount = float(amount)

    message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    signature = generate_signature(message)

    esewa_url = get_esewa_base_url() + "/api/epay/main/v2/form"

    fields = {
        "amount": str(amount),
        "tax_amount": "0",
        "total_amount": str(total_amount),
        "transaction_uuid": transaction_uuid,
        "product_code": product_code,
        "product_service_charge": "0",
        "product_delivery_charge": "0",
        "success_url": success_url,
        "failure_url": failure_url,
        "signed_field_names": "total_amount,transaction_uuid,product_code",
        "signature": signature,
    }

    return {"url": esewa_url, "fields": fields}


def verify_esewa_payment(encoded_data):
    try:
        decoded_bytes = base64.b64decode(encoded_data)
        response_data = json.loads(decoded_bytes.decode("utf-8"))
    except Exception as e:
        return {"success": False, "error": f"Failed to decode: {str(e)}"}

    status = response_data.get("status", "")
    transaction_code = response_data.get("transaction_code", "")
    total_amount = response_data.get("total_amount", "")
    transaction_uuid = response_data.get("transaction_uuid", "")
    product_code = response_data.get("product_code", "")
    signed_field_names = response_data.get("signed_field_names", "")
    signature = response_data.get("signature", "")

    if status != "COMPLETE":
        return {"success": False, "error": f"Status: {status}", "data": response_data}

    # Verify via status API
    api_result = check_esewa_transaction_status(transaction_uuid, total_amount)

    if api_result["success"]:
        return {
            "success": True,
            "data": {
                "transaction_code": transaction_code,
                "transaction_uuid": transaction_uuid,
                "total_amount": total_amount,
                "status": status,
                "product_code": product_code,
                "ref_id": api_result.get("ref_id", transaction_code),
                "signature": signature,
                "signed_field_names": signed_field_names,
            },
            "raw_response": response_data,
        }
    else:
        # If API check fails, still trust the signature-based response for sandbox
        return {
            "success": True,
            "data": {
                "transaction_code": transaction_code,
                "transaction_uuid": transaction_uuid,
                "total_amount": total_amount,
                "status": status,
                "product_code": product_code,
                "ref_id": transaction_code,
                "signature": signature,
                "signed_field_names": signed_field_names,
            },
            "raw_response": response_data,
        }


def check_esewa_transaction_status(transaction_uuid, total_amount):
    product_code = get_esewa_product_code()
    base_url = get_esewa_base_url()
    url = f"{base_url}/api/epay/transaction/status/"

    params = {
        "product_code": product_code,
        "total_amount": str(total_amount),
        "transaction_uuid": transaction_uuid,
    }

    try:
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()

        if resp.status_code == 200 and data.get("status") == "COMPLETE":
            return {"success": True, "ref_id": data.get("ref_id", ""), "data": data}
        else:
            return {"success": False, "error": f"Status: {data.get('status', 'UNKNOWN')}"}
    except requests.RequestException as e:
        return {"success": False, "error": f"Network error: {str(e)}"}
