"""
VNPay v2.1.0 Authoritative Specification Oracle.
Implements the reference VNPay payment URL builder, HMAC-SHA512 checksum calculator,
and server-to-server IPN response simulator according to official VNPay specifications.
"""

import hashlib
import hmac
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Tuple, Optional


DEFAULT_TMN_CODE = "MOCREST1"
DEFAULT_HASH_SECRET = "VNPAYSECRETKEY2026MOCRESTAURANT"
DEFAULT_SANDBOX_URL = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"


def calculate_hmac_sha512(params: Dict[str, Any], hash_secret: str) -> str:
    """
    Calculate HMAC-SHA512 checksum for VNPay parameters.
    Rules:
    - Exclude 'vnp_SecureHash' and 'vnp_SecureHashType'.
    - Exclude empty or None values.
    - Sort parameters by key in ASCII order.
    - Format key=value with urllib.parse.quote_plus.
    - Compute HMAC-SHA512 hex digest.
    """
    clean_params = {}
    for k, v in params.items():
        if k in ("vnp_SecureHash", "vnp_SecureHashType"):
            continue
        if v is not None and str(v) != "":
            clean_params[k] = str(v)

    sorted_items = sorted(clean_params.items())
    hash_data = "&".join(
        f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_items
    )
    return hmac.new(
        hash_secret.encode("utf-8"),
        hash_data.encode("utf-8"),
        hashlib.sha512
    ).hexdigest()


def verify_vnpay_signature(params: Dict[str, Any], secure_hash: str, hash_secret: str) -> bool:
    """Verify if the provided secure_hash matches the expected HMAC-SHA512."""
    if not secure_hash:
        return False
    expected_hash = calculate_hmac_sha512(params, hash_secret)
    return hmac.compare_digest(expected_hash.lower(), secure_hash.lower())


def build_vnpay_payment_url(
    txn_ref: str,
    amount_vnd: int,
    order_info: str,
    ip_addr: str = "127.0.0.1",
    tmn_code: str = DEFAULT_TMN_CODE,
    hash_secret: str = DEFAULT_HASH_SECRET,
    base_url: str = DEFAULT_SANDBOX_URL,
    return_url: str = "http://localhost:5173/payment/vnpay-return",
    locale: str = "vn",
    create_date: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Build a complete VNPay Sandbox redirect URL with vnp_SecureHash.
    """
    if create_date is None:
        create_date = datetime.now().strftime("%Y%m%d%H%M%S")

    params: Dict[str, Any] = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": tmn_code,
        "vnp_Amount": str(int(amount_vnd * 100)),
        "vnp_CreateDate": create_date,
        "vnp_CurrCode": "VND",
        "vnp_IpAddr": ip_addr,
        "vnp_Locale": locale,
        "vnp_OrderInfo": order_info,
        "vnp_OrderType": "billpayment",
        "vnp_ReturnUrl": return_url,
        "vnp_TxnRef": txn_ref,
    }

    checksum = calculate_hmac_sha512(params, hash_secret)
    params["vnp_SecureHash"] = checksum

    # Format query string
    sorted_items = sorted(params.items())
    query_string = "&".join(
        f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_items
    )
    full_url = f"{base_url}?{query_string}"
    return full_url, params


def evaluate_vnpay_ipn(
    query_params: Dict[str, Any],
    db_record: Optional[Dict[str, Any]],
    hash_secret: str = DEFAULT_HASH_SECRET,
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Evaluate VNPay IPN webhook callback according to official IPN specification:
    Response Codes:
    - '00': Confirm Success
    - '01': Order not found
    - '02': Order already confirmed
    - '04': Invalid amount
    - '97': Invalid Checksum
    """
    params = dict(query_params)
    vnp_secure_hash = params.pop("vnp_SecureHash", None)
    params.pop("vnp_SecureHashType", None)

    # 1. Verify Checksum
    if not vnp_secure_hash or not verify_vnpay_signature(params, vnp_secure_hash, hash_secret):
        return "97", "Invalid Checksum", {}

    txn_ref = params.get("vnp_TxnRef")
    amount = int(params.get("vnp_Amount", 0))
    response_code = params.get("vnp_ResponseCode")

    # 2. Verify Order Existence
    if db_record is None or db_record.get("ma_giao_dich") != txn_ref:
        return "01", "Order not found", {}

    # 3. Verify Amount (VNPay sends amount * 100)
    expected_amount = int(db_record.get("so_tien", 0) * 100)
    if amount != expected_amount:
        return "04", "Invalid amount", {}

    # 4. Check Idempotency (Already confirmed)
    current_status = db_record.get("trang_thai")
    if current_status in ("thanh_cong", "da_xac_nhan"):
        return "02", "Order already confirmed", db_record

    # 5. Success or Failure update
    updated_record = dict(db_record)
    if response_code == "00":
        updated_record["trang_thai"] = "thanh_cong"
        updated_record["thanh_toan_luc"] = datetime.now().isoformat()
        return "00", "Confirm Success", updated_record
    else:
        updated_record["trang_thai"] = "that_bai"
        return "00", "Confirm Failure", updated_record
