import logging
import resend
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import escape

logger = logging.getLogger(__name__)


def gui_email_xac_thuc(thu_dien_tu: str, ten_nguoi_nhan: str, ma_otp: str) -> bool:
    """
    Gửi email chứa mã xác thực OTP qua Resend API (nếu RESEND_API_KEY được cấu hình).
    Fallback sang Django send_mail (console/configured backend) nếu chưa có key hoặc gặp lỗi.
    """
    resend_api_key = getattr(settings, "RESEND_API_KEY", "") or ""
    from_email = getattr(settings, "RESEND_FROM_EMAIL", "onboarding@resend.dev")

    tieu_de = f"[{ma_otp}] Mã xác thực tài khoản Nhà hàng Mộc"
    ten_html = escape(ten_nguoi_nhan or "Quý khách")

    noi_dung_html = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Xác thực tài khoản</title>
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f7f7f5; margin: 0; padding: 24px; color: #1c1c1a; }}
        .card {{ max-width: 500px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 32px; border: 1px solid #ebebea; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
        .header {{ text-align: center; border-bottom: 1px solid #f0f0ee; padding-bottom: 20px; margin-bottom: 24px; }}
        .header h1 {{ margin: 0; font-size: 24px; color: #b43826; }}
        .otp-box {{ background-color: #fdf6f0; border: 2px dashed #b43826; border-radius: 12px; padding: 20px; text-align: center; margin: 28px 0; }}
        .otp-code {{ font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #b43826; font-family: monospace; }}
        .footer {{ text-align: center; font-size: 13px; color: #767571; margin-top: 32px; border-top: 1px solid #f0f0ee; padding-top: 16px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <h1>🌿 Nhà Hàng Mộc</h1>
        </div>
        <p>Xin chào <strong>{ten_html}</strong>,</p>
        <p>Cảm ơn bạn đã đăng ký tài khoản tại Nhà hàng Mộc. Dưới đây là mã xác thực tài khoản của bạn:</p>
        
        <div class="otp-box">
          <div class="otp-code">{ma_otp}</div>
        </div>

        <p style="font-size: 14px; color: #767571;">
          ⏱️ Mã xác thực có hiệu lực trong <strong>15 phút</strong>. Vui lòng không chia sẻ mã này cho bất kỳ ai.
        </p>

        <div class="footer">
          Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email.<br>
          © 2026 Nhà hàng Mộc. Mọi quyền được bảo lưu.
        </div>
      </div>
    </body>
    </html>
    """

    noi_dung_text = (
        f"Chào {ten_nguoi_nhan or 'Quý khách'},\n\n"
        f"Mã xác thực tài khoản Nhà hàng Mộc của bạn là: {ma_otp}\n\n"
        f"Mã có hiệu lực trong vòng 15 phút. Vui lòng không chia sẻ mã này cho ai khác.\n\n"
        f"Nhà hàng Mộc trân trọng cảm ơn!"
    )

    if resend_api_key and not resend_api_key.startswith("re_your_api_key"):
        try:
            resend.api_key = resend_api_key
            params = {
                "from": from_email,
                "to": [thu_dien_tu],
                "subject": tieu_de,
                "html": noi_dung_html,
                "text": noi_dung_text,
            }
            res = resend.Emails.send(params)
            logger.info("Đã gửi email xác thực thành công qua Resend: %s (id: %s)", thu_dien_tu, res)
            return True
        except Exception as e:
            logger.warning("Gửi qua Resend thất bại (%s), chuyển sang console/Django mailer.", e)

    # Fallback sang send_mail
    try:
        send_mail(
            subject=tieu_de,
            message=noi_dung_text,
            html_message=noi_dung_html,
            from_email=from_email,
            recipient_list=[thu_dien_tu],
            fail_silently=True,
        )
        logger.info("Đã gửi email xác thực qua Django mailer fallback: %s", thu_dien_tu)
        return True
    except Exception as e:
        logger.error("Lỗi khi gửi email xác thực: %s", e)
        return False
