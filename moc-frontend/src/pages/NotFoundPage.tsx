import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="max-w-lg mx-auto px-5 py-28 text-center">
      <div className="font-display text-6xl text-primary mb-4">404</div>
      <h1 className="font-display text-2xl mb-3">Không tìm thấy trang</h1>
      <p className="text-muted mb-8">Trang bạn tìm không tồn tại hoặc đã được di chuyển.</p>
      <Link to="/" className="btn btn-primary">Về trang chủ</Link>
    </div>
  );
}
