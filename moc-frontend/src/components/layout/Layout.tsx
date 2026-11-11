import { Outlet, useLocation } from "react-router-dom";
import { useEffect } from "react";
import Header from "./Header";
import Footer from "./Footer";
import ChatWidget from "@/components/chat/ChatWidget";

export default function Layout() {
  const { pathname, hash } = useLocation();

  // Sang trang mới thì về đầu trang; có #muc thì cuộn tới mục đó (vd. /chinh-sach-bao-mat#tro-ly-ai).
  useEffect(() => {
    const muc = hash && document.getElementById(decodeURIComponent(hash.slice(1)));
    if (muc) muc.scrollIntoView();
    else window.scrollTo(0, 0);
  }, [pathname, hash]);

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <ChatWidget />
    </div>
  );
}
