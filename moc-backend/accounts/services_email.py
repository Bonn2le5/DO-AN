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

    return _gui(thu_dien_tu, tieu_de, noi_dung_html, noi_dung_text)


def _gui(thu_dien_tu: str, tieu_de: str, noi_dung_html: str, noi_dung_text: str) -> bool:
    resend_api_key = getattr(settings, "RESEND_API_KEY", "") or ""
    from_email = getattr(settings, "RESEND_FROM_EMAIL", "onboarding@resend.dev")

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
            logger.info("Đã gửi email qua Resend: %s (id: %s)", thu_dien_tu, res)
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
        logger.info("Đã gửi email qua Django mailer fallback: %s", thu_dien_tu)
        return True
    except Exception as e:
        logger.error("Lỗi khi gửi email: %s", e)
        return False


_NEN = "margin:0;padding:32px 16px;background:#f4f5f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;color:#1c1c1a"
_THE = "max-width:480px;margin:0 auto 20px;background:#ffffff;border-radius:28px;padding:40px 36px;text-align:center"


def an_email(thu_dien_tu: str) -> str:
    """vuvan200705@gmail.com -> vuv********@gm***.com"""
    phan_ten, _, ten_mien = thu_dien_tu.partition("@")
    ten, _, duoi = ten_mien.rpartition(".")
    return f"{phan_ten[:3]}{'*' * max(len(phan_ten) - 3, 1)}@{ten[:2]}***.{duoi}"


def gui_ma_otp(thu_dien_tu: str, ma_otp: str) -> bool:
    """Mail "Mã xác minh": dùng cho đổi email (gửi tới email mới) và quên mật khẩu."""
    ho_tro = escape(getattr(settings, "FRONTEND_URL", ""))
    noi_dung_html = f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="{_NEN}">
  <div style="{_THE}">
    <h1 style="margin:0 0 16px;font-size:30px;font-weight:700">Mã xác minh</h1>
    <p style="margin:0 auto;max-width:360px;font-size:17px;line-height:1.6;color:#767676">
      Mã này sẽ hết hạn sau 15 phút và chỉ có thể được sử dụng một lần. Đừng bao giờ chia sẻ mã này với bất kỳ ai.
    </p>
    <div style="margin-top:36px;font-size:52px;font-weight:600;letter-spacing:2px">{ma_otp[:3]} {ma_otp[3:]}</div>
  </div>
  <div style="{_THE};text-align:left;padding:36px">
    <p style="margin:0 0 6px;font-size:17px;font-weight:600">&#10067; Bạn không nhận ra hoạt động này?</p>
    <p style="margin:0;font-size:16px;line-height:1.6;color:#767676">
      Nếu bạn cho rằng mình nhận được email này do nhầm lẫn, hãy
      <a href="{ho_tro}" style="color:#767676">truy cập bộ phận hỗ trợ</a>.
    </p>
  </div>
</body></html>"""
    noi_dung_text = (
        f"Mã xác minh Mộc Kitchen của bạn: {ma_otp}\n\n"
        "Mã hết hạn sau 15 phút và chỉ dùng được một lần. Đừng chia sẻ mã này với bất kỳ ai.\n"
        "Nếu bạn không yêu cầu, hãy bỏ qua email này."
    )
    return _gui(thu_dien_tu, "[Mộc Kitchen Accounts] - Mã xác thực OTP", noi_dung_html, noi_dung_text)


def gui_thong_bao_doi_email(email_cu: str, email_moi: str) -> bool:
    """Thư báo gửi về email CŨ sau khi đổi xong, để chủ tài khoản phát hiện nếu bị chiếm."""
    ho_tro = escape(getattr(settings, "FRONTEND_URL", ""))
    cu, moi = an_email(email_cu), an_email(email_moi)
    noi_dung_html = f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:40px 16px;background:#f0f0f0;font-family:Arial,Helvetica,sans-serif;color:#1c1c1a">
  <div style="max-width:560px;margin:0 auto;text-align:center">
    <div style="width:56px;height:56px;margin:0 auto 24px;border-radius:50%;background:#b43826;color:#fff;font-size:26px;line-height:56px;font-weight:700">M</div>
    <h1 style="margin:0 0 36px;font-size:32px;font-weight:400;line-height:1.3">Bạn Đã Thay Đổi Địa Chỉ Email Của Mình</h1>
    <div style="background:#f9f9f9;padding:40px 28px;font-size:17px;line-height:1.6;color:#666">
      Chúng tôi đã thay đổi địa chỉ email cho tài khoản Mộc Kitchen của bạn thành công.<br>
      <strong>Cũ:</strong> {cu}<br>
      <strong>Mới:</strong> {moi}<br>
      Nếu bạn không yêu cầu thực hiện thay đổi này,<br>
      vui lòng liên hệ với <a href="{ho_tro}" style="color:#b43826">Đội Ngũ Hỗ Trợ Mộc Kitchen</a>.
    </div>
  </div>
</body></html>"""
    noi_dung_text = (
        "Chúng tôi đã thay đổi địa chỉ email cho tài khoản Mộc Kitchen của bạn thành công.\n"
        f"Cũ: {cu}\nMới: {moi}\n\n"
        "Nếu bạn không yêu cầu thực hiện thay đổi này, vui lòng liên hệ Đội Ngũ Hỗ Trợ Mộc Kitchen."
    )
    return _gui(email_cu, "Bạn Đã Thay Đổi Địa Chỉ Email Của Mình", noi_dung_html, noi_dung_text)
