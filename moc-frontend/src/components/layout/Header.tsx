import { useEffect, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { Search, Heart, User, Menu, X } from "lucide-react";
import { useFavoriteStore } from "@/store/favoriteStore";
import { useAuthStore } from "@/store/authStore";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { to: "/", label: "Trang chủ" },
  { to: "/thuc-don", label: "Thực đơn" },
  { to: "/dat-ban", label: "Đặt bàn" },
  { to: "/chi-nhanh", label: "Chi nhánh" },
  { to: "/khuyen-mai", label: "Khuyến mãi" },
  { to: "/bai-viet", label: "Bài viết" },
];

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const favCount = useFavoriteStore((s) => s.count());
  const { isAuthenticated, user } = useAuthStore();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={cn(
        "sticky top-0 z-50 bg-wine text-white border-b border-white/10 transition-all duration-300",
        scrolled && "shadow-[0_6px_24px_rgba(60,15,15,0.35)]",
      )}
    >
      <div className="max-w-310 mx-auto px-5 md:px-8">
        <div
          className={cn(
            "flex items-center justify-between transition-all duration-300",
            scrolled ? "h-17.5" : "h-20.5",
          )}
        >
          <Link
            to="/"
            className="font-serif text-[28px] font-semibold flex items-baseline gap-2 text-white"
          >
            MỘC
            <span className="font-body text-[9.5px] font-bold tracking-[0.18em] text-white/60 uppercase">
              Kitchen
            </span>
          </Link>

          <nav className="hidden md:flex gap-1.5">
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  cn(
                    "text-[14.5px] font-medium px-3.5 py-1.5 rounded-md text-white/85 hover:text-white hover:bg-white/10 transition-colors",
                    isActive && "bg-gold text-wine-dark hover:bg-gold hover:text-wine-dark",
                  )
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-1">
            <Link
              to="/thuc-don?focusSearch=1"
              className="icon-btn text-white! hover:bg-white/10!"
              title="Tìm kiếm món ăn"
              aria-label="Tìm kiếm món ăn"
            >
              <Search width={19} height={19} />
            </Link>
            {isAuthenticated && (
              <Link
                to="/tai-khoan/yeu-thich"
                className="icon-btn text-white! hover:bg-white/10! relative"
                title="Yêu thích"
                aria-label="Yêu thích"
              >
                <Heart width={19} height={19} />
                {favCount > 0 && <Badge count={favCount} />}
              </Link>
            )}
            <Link
              to={isAuthenticated ? "/tai-khoan" : "/dang-nhap"}
              className="icon-btn text-white! hover:bg-white/10!"
              title="Tài khoản"
            >
              {isAuthenticated && user ? (
                <span className="w-7 h-7 rounded-full bg-gold text-wine-dark text-xs font-bold flex items-center justify-center">
                  {user.avatarInitial}
                </span>
              ) : (
                <User width={19} height={19} />
              )}
            </Link>
            {isAuthenticated && user?.isStaff && (
              <Link
                to="/admin"
                className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-white text-wine text-xs font-semibold hover:bg-gold hover:text-wine-dark transition-colors ml-1.5 shadow-sm"
                title="Vào trang quản trị"
              >
                Quản trị
              </Link>
            )}
          </div>

          <button
            className="md:hidden w-10 h-10 flex items-center justify-center rounded-full hover:bg-white/10"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label={mobileOpen ? "Đóng menu" : "Mở menu"}
            aria-expanded={mobileOpen}
          >
            {mobileOpen ? (
              <X width={20} height={20} />
            ) : (
              <Menu width={20} height={20} />
            )}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden border-t border-white/10 bg-wine-dark px-5 py-5">
          <nav className="flex flex-col gap-1">
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) => cn("py-3 text-[15px] font-medium border-b border-white/10 last:border-0", isActive ? "text-gold" : "text-white/90")}
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-3 mt-5">
            <Link
              to={isAuthenticated ? "/tai-khoan" : "/dang-nhap"}
              onClick={() => setMobileOpen(false)}
              className="btn flex-1 border-[1.5px] border-white/70 text-white hover:bg-white hover:text-wine rounded-md"
            >
              Tài khoản
            </Link>
          </div>
          <div className="flex items-center justify-center gap-6 mt-4 text-sm text-white/85">
            <Link
              to="/thuc-don?focusSearch=1"
              onClick={() => setMobileOpen(false)}
              className="inline-flex items-center gap-2 py-2"
            >
              <Search size={17} /> Tìm món
            </Link>
            {isAuthenticated && (
              <Link
                to="/tai-khoan/yeu-thich"
                onClick={() => setMobileOpen(false)}
                className="inline-flex items-center gap-2 py-2"
              >
                <Heart size={17} /> Yêu thích{favCount > 0 ? ` (${favCount})` : ""}
              </Link>
            )}
          </div>
        </div>
      )}
    </header>
  );
}

function Badge({ count }: { count: number }) {
  return (
    <span className="absolute top-0.5 right-0.5 min-w-4 h-4 px-1 rounded-full bg-gold text-wine-dark text-[9.5px] font-bold flex items-center justify-center">
      {count}
    </span>
  );
}
