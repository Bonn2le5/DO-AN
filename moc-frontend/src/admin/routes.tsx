import { lazy } from "react";
import { Route } from "react-router-dom";
import AdminGuard from "./layout/AdminGuard";
import AdminLayout from "./layout/AdminLayout";

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

/** Đặt {adminRoutes} trong <Routes> của App.tsx, NGOÀI <Route element={<Layout />}> để không dính header/footer của khách. */
export const adminRoutes = (
  <Route path="admin" element={<AdminGuard />}>
    <Route element={<AdminLayout />}>
      <Route index element={<Dashboard />} />
      <Route path="orders" element={<Orders />} />
      <Route path="reservations" element={<Reservations />} />
      <Route path="tables" element={<Tables />} />
      <Route path="chat" element={<Chat />} />
      <Route path="menu" element={<Foods />} />
      <Route path="categories" element={<Categories />} />
      <Route path="ingredients" element={<Ingredients />} />
      <Route path="promotions" element={<Promotions />} />
      <Route path="posts" element={<Posts />} />
      <Route path="reviews" element={<Reviews />} />
      <Route path="payments" element={<Payments />} />
      <Route path="deposit-policy" element={<DepositPolicy />} />
      <Route path="branches" element={<Branches />} />
      <Route path="users" element={<Users />} />
      <Route path="roles" element={<Roles />} />
      <Route path="ai" element={<Ai />} />
      <Route path="settings" element={<Settings />} />
    </Route>
  </Route>
);
