import { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "@/components/layout/Layout";
import AccountLayout from "@/components/layout/AccountLayout";
import HomePage from "@/pages/home/HomePage";
import MenuPage from "@/pages/menu/MenuPage";
import FoodDetailPage from "@/pages/food-detail/FoodDetailPage";
import CheckoutPage from "@/pages/checkout/CheckoutPage";
import OrderSuccessPage from "@/pages/order/OrderSuccessPage";
import ReservationPage from "@/pages/reservation/ReservationPage";
import ReservationPaymentResultPage from "@/pages/reservation/ReservationPaymentResultPage";
import PromotionsPage from "@/pages/promotions/PromotionsPage";
import BlogPage from "@/pages/blog/BlogPage";
import BlogDetailPage from "@/pages/blog/BlogDetailPage";
import LoginPage from "@/pages/auth/LoginPage";
import RegisterPage from "@/pages/auth/RegisterPage";
import EmailVerificationPage from "@/pages/auth/EmailVerificationPage";
import AccountProfilePage from "@/pages/account/AccountProfilePage";
import AccountOrdersPage from "@/pages/account/AccountOrdersPage";
import AccountFavoritesPage from "@/pages/account/AccountFavoritesPage";
import NotFoundPage from "@/pages/NotFoundPage";

import { adminRoutes } from "@/admin/routes";

// Leaflet (~150kb) is only needed on this one page, so it's code-split into
// its own chunk instead of bloating the main bundle every visitor downloads.
const LocationPage = lazy(() => import("@/pages/location/LocationPage"));

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {adminRoutes}

        {/* Customer Routes */}
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="thuc-don" element={<MenuPage />} />
          <Route path="thuc-don/:slug" element={<FoodDetailPage />} />
          <Route path="thanh-toan" element={<CheckoutPage />} />
          <Route path="don-hang/thanh-cong" element={<OrderSuccessPage />} />
          <Route path="dat-ban" element={<ReservationPage />} />
          <Route path="dat-ban/thanh-toan-ket-qua" element={<ReservationPaymentResultPage />} />
          <Route
            path="chi-nhanh"
            element={
              <Suspense
                fallback={
                  <div className="max-w-310 mx-auto px-5 py-24 text-center text-muted">
                    Đang tải bản đồ...
                  </div>
                }
              >
                <LocationPage />
              </Suspense>
            }
          />
          <Route path="khuyen-mai" element={<PromotionsPage />} />
          <Route path="bai-viet" element={<BlogPage />} />
          <Route path="bai-viet/:slug" element={<BlogDetailPage />} />
          <Route path="dang-nhap" element={<LoginPage />} />
          <Route path="dang-ky" element={<RegisterPage />} />
          <Route path="auth/verify-email" element={<EmailVerificationPage />} />
          <Route path="tai-khoan" element={<AccountLayout />}>
            <Route index element={<AccountProfilePage />} />
            <Route path="don-hang" element={<AccountOrdersPage />} />
            <Route path="yeu-thich" element={<AccountFavoritesPage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
