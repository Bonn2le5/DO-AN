import { Link } from "react-router-dom";
import { Newspaper } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getBlogPosts } from "@/api/blog.api";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";
import { formatDate } from "@/lib/utils";

export default function BlogPage() {
  const { data: posts, loading } = useAsync(getBlogPosts);

  return (
    <div className="max-w-[1100px] mx-auto px-5 md:px-8 py-12">
      <div className="mb-10">
        <div className="eyebrow">Bài viết</div>
        <h1 className="font-display text-[32px] sm:text-[38px]">Câu chuyện từ căn bếp</h1>
      </div>

      {loading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="rounded-[18px] h-[280px] bg-black/[0.05] animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {posts?.map((post) => (
            <Link key={post.id} to={`/bai-viet/${post.slug}`} className="card overflow-hidden hover:shadow-lift transition-shadow">
              <div className="aspect-[16/10]">
                <PlaceholderMedia tone={post.placeholderTone} icon={Newspaper} className="w-full h-full" iconClassName="w-8 h-8" />
              </div>
              <div className="p-5">
                <div className="text-[11px] font-bold uppercase tracking-wide text-primary">{post.tag}</div>
                <h3 className="font-display text-lg mt-2 mb-2.5 leading-snug">{post.title}</h3>
                <p className="text-[13px] text-muted mb-3 line-clamp-2">{post.excerpt}</p>
                <div className="text-xs text-muted">{formatDate(post.createdAt)} · {post.readMinutes} phút đọc</div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
