import { lazy } from "react";
import { Navigate, Route } from "react-router-dom";
import type { ReactNode } from "react";
import AdminGuard from "./layout/AdminGuard";
import AdminLayout from "./layout/AdminLayout";
import { useCan } from "./permissions";
import type { Module } from "./types";

const page = (loader: () => Promise<{ default: React.ComponentType }>) => lazy(loader);
const Dashboard = page(() => import("./pages/DashboardPage"));
const Orders = page(() => import("./pages/OrdersPage"));
const Reservations = page(() => import("./pages/ReservationsPage"));
const Tables = page(() => import("./pages/TablesPage"));
const Chat = page(() => import("./pages/ChatPage"));
const Foods = page(() => import("./pages/FoodsPage"));
const Categories = page(() => import("./pages/CategoriesPage"));
const Ingredients = page(() => import("./pages/IngredientsPage"));
const Promotions = page(() => import("./pages/PromotionsPage"));
const Posts = page(() => import("./pages/PostsPage"));
const Reviews = page(() => import("./pages/ReviewsPage"));
const Payments = page(() => import("./pages/PaymentsPage"));
const DepositPolicy = page(() => import("./pages/DepositPolicyPage"));
const Branches = page(() => import("./pages/BranchesPage"));
const Users = page(() => import("./pages/UsersPage"));
const Roles = page(() => import("./pages/RolesPage"));
const Ai = page(() => import("./pages/AiAnalyticsPage"));
const Settings = page(() => import("./pages/SettingsPage"));

function ModuleGate({ module, children }: { module: Module; children: ReactNode }) {
  const can = useCan();
  if (can(module)) return children;
  return <Navigate to={module === "dashboard" ? "/admin/dat-ban" : "/admin"} replace />;
}

/** Đặt {adminRoutes} trong <Routes> của App.tsx, NGOÀI <Route element={<Layout />}> để không dính header/footer của khách. */
export const adminRoutes = (
  <Route path="admin" element={<AdminGuard />}>
    <Route element={<AdminLayout />}>
      <Route index element={<ModuleGate module="dashboard"><Dashboard /></ModuleGate>} />
      <Route path="don-hang" element={<ModuleGate module="orders"><Orders /></ModuleGate>} />
      <Route path="dat-ban" element={<ModuleGate module="reservations"><Reservations /></ModuleGate>} />
      <Route path="ban-an" element={<ModuleGate module="tables"><Tables /></ModuleGate>} />
      <Route path="hoi-thoai" element={<ModuleGate module="chat"><Chat /></ModuleGate>} />
      <Route path="mon-an" element={<ModuleGate module="foods"><Foods /></ModuleGate>} />
      <Route path="danh-muc" element={<ModuleGate module="categories"><Categories /></ModuleGate>} />
      <Route path="nguyen-lieu" element={<ModuleGate module="ingredients"><Ingredients /></ModuleGate>} />
      <Route path="khuyen-mai" element={<ModuleGate module="promotions"><Promotions /></ModuleGate>} />
      <Route path="bai-viet" element={<ModuleGate module="posts"><Posts /></ModuleGate>} />
      <Route path="danh-gia" element={<ModuleGate module="reviews"><Reviews /></ModuleGate>} />
      <Route path="thanh-toan" element={<ModuleGate module="payments"><Payments /></ModuleGate>} />
      <Route path="chinh-sach-coc" element={<ModuleGate module="deposit"><DepositPolicy /></ModuleGate>} />
      <Route path="chi-nhanh" element={<ModuleGate module="branches"><Branches /></ModuleGate>} />
      <Route path="nguoi-dung" element={<ModuleGate module="users"><Users /></ModuleGate>} />
      <Route path="vai-tro" element={<ModuleGate module="roles"><Roles /></ModuleGate>} />
      <Route path="ai" element={<ModuleGate module="ai"><Ai /></ModuleGate>} />
      <Route path="cai-dat" element={<ModuleGate module="settings"><Settings /></ModuleGate>} />
    </Route>
  </Route>
);
