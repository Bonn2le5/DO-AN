import { useEffect, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { Search, Heart, ShoppingCart, User, Menu, X } from "lucide-react";
import { useCartStore } from "@/store/cartStore";
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
  const itemCount = useCartStore((s) => s.itemCount());
  const openDrawer = useCartStore((s) => s.openDrawer);
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
        "sticky top-0 z-50 backdrop-blur-xl transition-all duration-300",
        scrolled
          ? "bg-bg/95 border-b border-black/[0.07] shadow-[0_4px_24px_rgba(23,23,23,0.05)]"
          : "bg-bg/70 border-b border-transparent",
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
            className="font-display text-2xl font-semibold flex items-baseline gap-2"
          >
            MỘC
            <span className="font-body text-[9.5px] font-bold tracking-[0.18em] text-muted uppercase">
              Kitchen
            </span>
          </Link>

          <nav className="hidden md:flex gap-9">
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  cn(
                    "text-[14.5px] font-medium relative py-1.5 hover:text-primary transition-colors",
                    isActive && "text-primary",
                  )
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-1">
            <button className="icon-btn" title="Tìm kiếm">
              <Search width={19} height={19} />
            </button>
            <Link
              to="/tai-khoan/yeu-thich"
              className="icon-btn relative"
              title="Yêu thích"
            >
              <Heart width={19} height={19} />
              {favCount > 0 && <Badge count={favCount} />}
            </Link>
            <button
              onClick={openDrawer}
              className="icon-btn relative"
              title="Giỏ hàng"
            >
              <ShoppingCart width={19} height={19} />
              {itemCount > 0 && <Badge count={itemCount} />}
            </button>
            <Link
              to={isAuthenticated ? "/tai-khoan" : "/dang-nhap"}
              className="icon-btn"
              title="Tài khoản"
            >
              {isAuthenticated && user ? (
                <span className="w-7 h-7 rounded-full bg-primary text-white text-xs font-bold flex items-center justify-center">
                  {user.avatarInitial}
                </span>
              ) : (
                <User width={19} height={19} />
              )}
            </Link>
            {isAuthenticated && user?.isStaff && (
              <Link
                to="/admin"
                className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-dark text-white text-xs font-semibold hover:bg-black transition-colors ml-1.5 shadow-sm"
                title="Vào trang quản trị"
              >
                Quản trị
              </Link>
            )}
          </div>

          <button
            className="md:hidden w-10 h-10 flex items-center justify-center rounded-full hover:bg-black/5"
            onClick={() => setMobileOpen((v) => !v)}
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
        <div className="md:hidden border-t border-black/[0.07] bg-bg px-5 py-5">
          <nav className="flex flex-col gap-1">
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                onClick={() => setMobileOpen(false)}
                className="py-3 text-[15px] font-medium border-b border-black/5 last:border-0"
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-3 mt-5">
            <button
              onClick={() => {
                openDrawer();
                setMobileOpen(false);
              }}
              className="btn btn-primary flex-1"
            >
              Giỏ hàng ({itemCount})
            </button>
            <Link
              to={isAuthenticated ? "/tai-khoan" : "/dang-nhap"}
              onClick={() => setMobileOpen(false)}
              className="btn btn-outline flex-1"
            >
              Tài khoản
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}

function Badge({ count }: { count: number }) {
  return (
    <span className="absolute top-0.5 right-0.5 min-w-4 h-4 px-1 rounded-full bg-primary text-white text-[9.5px] font-bold flex items-center justify-center">
      {count}
    </span>
  );
}
