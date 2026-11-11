import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";
import { fileURLToPath } from "url";

const rootDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(rootDir, "./src"),
    },
  },
  // react-leaflet chỉ được import trong trang Chi nhánh (lazy). Nếu không khai báo ở đây,
  // Vite phát hiện muộn và bundle lại deps giữa chừng → trang dùng 2 bản React khác nhau
  // ("Invalid hook call") và cả app trắng trang.
  optimizeDeps: {
    include: ["leaflet", "react-leaflet"],
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/media": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
