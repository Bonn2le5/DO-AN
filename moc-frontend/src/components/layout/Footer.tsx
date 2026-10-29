import { Link } from "react-router-dom";

// lucide-react no longer ships brand/social glyphs, so these two are inlined.
function InstagramIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect x="3" y="3" width="18" height="18" rx="5" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none" />
    </svg>
  );
}
function FacebookIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M18 2h-3a5 5 0 00-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 011-1h3z" />
    </svg>
  );
}

export default function Footer() {
  return (
    <footer className="bg-dark text-white/70 pt-20">
      <div className="max-w-[1240px] mx-auto px-5 md:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 md:gap-12 pb-14 border-b border-white/10">
          <div>
            <div className="font-display text-2xl text-white mb-3.5">MỘC</div>
            <p className="text-[13.5px] leading-relaxed max-w-[280px]">
              Ẩm thực Việt hiện đại giữa lòng thành phố — nơi mỗi món ăn là một câu chuyện.
            </p>
            <div className="flex gap-2.5 mt-5">
              <a href="#" className="w-9 h-9 rounded-full border border-white/20 flex items-center justify-center hover:border-white/50 transition-colors">
                <InstagramIcon />
              </a>
              <a href="#" className="w-9 h-9 rounded-full border border-white/20 flex items-center justify-center hover:border-white/50 transition-colors">
                <FacebookIcon />
              </a>
            </div>
          </div>
          <div>
            <h5 className="text-white text-[13px] uppercase tracking-wide mb-4">Điều hướng</h5>
            <ul className="space-y-2.5 text-sm">
              <li><Link to="/" className="hover:text-secondary transition-colors">Trang chủ</Link></li>
              <li><Link to="/thuc-don" className="hover:text-secondary transition-colors">Thực đơn</Link></li>
          <li><Link to="/chi-nhanh" className="hover:text-secondary transition-colors">Chi nhánh</Link></li>
              <li><Link to="/khuyen-mai" className="hover:text-secondary transition-colors">Khuyến mãi</Link></li>
              <li><Link to="/bai-viet" className="hover:text-secondary transition-colors">Bài viết</Link></li>
            </ul>
          </div>
          <div>
            <h5 className="text-white text-[13px] uppercase tracking-wide mb-4">Liên hệ</h5>
            <ul className="space-y-2.5 text-sm">
              <li>236B Lê Văn Sỹ, Tân Sơn Hòa, TP.HCM</li>
              <li>hello@moc-kitchen.vn</li>
              <li>+84 28 3822 1234</li>
            </ul>
          </div>
          <div>
            <h5 className="text-white text-[13px] uppercase tracking-wide mb-4">Giờ mở cửa</h5>
            <ul className="space-y-2.5 text-sm">
              <li>Thứ 2 – Thứ 6: 10:00 – 22:00</li>
              <li>Thứ 7 – CN: 09:00 – 23:00</li>
            </ul>
            <h5 className="text-white text-[13px] uppercase tracking-wide mt-6 mb-3">Nhận ưu đãi mới</h5>
            <form
              onSubmit={(e) => e.preventDefault()}
              className="flex items-center border border-white/20 rounded-full pl-4 pr-1 py-1"
            >
              <input
                type="email"
                required
                placeholder="Email của bạn"
                className="bg-transparent outline-none text-sm text-white placeholder:text-white/40 flex-1 min-w-0"
              />
              <button className="bg-primary text-white text-xs font-semibold px-4 py-2 rounded-full whitespace-nowrap">
                Đăng ký
              </button>
            </form>
          </div>
        </div>
        <div className="flex flex-col sm:flex-row justify-between gap-2 py-6 text-[12.5px] text-white/45">
          <span>© 2026 MỘC Kitchen. All rights reserved.</span>
          <span>Điều khoản · Chính sách bảo mật</span>
        </div>
      </div>
    </footer>
  );
}
