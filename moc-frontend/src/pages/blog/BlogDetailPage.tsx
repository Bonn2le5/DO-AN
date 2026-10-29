import { Link, useParams } from "react-router-dom";
import { ChevronRight, Newspaper } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getBlogPostBySlug, getOtherBlogPosts } from "@/api/blog.api";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";
import { formatDate } from "@/lib/utils";
import NotFoundPage from "@/pages/NotFoundPage";

export default function BlogDetailPage() {
  const { slug } = useParams();
  const { data: post, loading } = useAsync(() => getBlogPostBySlug(slug!), [slug]);
  const { data: others } = useAsync(() => (post ? getOtherBlogPosts(post.id) : Promise.resolve([])), [post?.id]);

  if (loading) {
    return (
      <div className="max-w-[760px] mx-auto px-5 md:px-8 py-12 space-y-4">
        <div className="h-6 w-40 bg-black/[0.05] rounded animate-pulse" />
        <div className="h-10 w-full bg-black/[0.05] rounded animate-pulse" />
        <div className="aspect-[16/9] rounded-[20px] bg-black/[0.05] animate-pulse" />
      </div>
    );
  }

  if (!post) return <NotFoundPage />;

  return (
    <div className="max-w-[760px] mx-auto px-5 md:px-8 py-12">
      <div className="flex items-center gap-1.5 text-[13px] text-muted mb-8">
        <Link to="/" className="hover:text-primary">Trang chủ</Link>
        <ChevronRight width={13} height={13} />
        <Link to="/bai-viet" className="hover:text-primary">Bài viết</Link>
      </div>

      <div className="text-[11px] font-bold uppercase tracking-wide text-primary mb-3">{post.tag}</div>
      <h1 className="font-display text-[30px] sm:text-[38px] leading-tight mb-4">{post.title}</h1>
      <div className="text-sm text-muted mb-8">
        {post.author} · {formatDate(post.createdAt)} · {post.readMinutes} phút đọc
      </div>

      <div className="aspect-[16/9] rounded-[20px] overflow-hidden mb-10">
        <PlaceholderMedia tone={post.placeholderTone} icon={Newspaper} className="w-full h-full" iconClassName="w-14 h-14" />
      </div>

      <div className="text-[16px] leading-[1.85] text-text space-y-5">
        <p>{post.content}</p>
      </div>

      {others && others.length > 0 && (
        <div className="mt-16 pt-10 border-t border-black/[0.08]">
          <h2 className="font-display text-xl mb-5">Bài viết khác</h2>
          <div className="grid sm:grid-cols-2 gap-5">
            {others.map((o) => (
              <Link key={o.id} to={`/bai-viet/${o.slug}`} className="card overflow-hidden hover:shadow-lift transition-shadow">
                <div className="aspect-[16/10]">
                  <PlaceholderMedia tone={o.placeholderTone} icon={Newspaper} className="w-full h-full" iconClassName="w-7 h-7" />
                </div>
                <div className="p-4">
                  <h3 className="font-display text-base leading-snug">{o.title}</h3>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
