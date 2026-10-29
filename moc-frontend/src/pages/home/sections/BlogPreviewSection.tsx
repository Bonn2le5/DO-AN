import { Link } from "react-router-dom";
import { Newspaper } from "lucide-react";
import SectionHeading from "@/components/ui/SectionHeading";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";
import { useAsync } from "@/hooks/useAsync";
import { getBlogPosts } from "@/api/blog.api";

export default function BlogPreviewSection() {
  const { data: posts, loading } = useAsync(getBlogPosts);

  return (
    <section className="py-20">
      <div className="max-w-310 mx-auto px-5 md:px-8">
        <SectionHeading
          eyebrow="Bài viết"
          title="Câu chuyện từ căn bếp"
          linkTo="/bai-viet"
        />
        {loading ? (
          <div className="grid md:grid-cols-3 gap-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="rounded-card-[260px] bg-black/5 animate-pulse"
              />
            ))}
          </div>
        ) : (
          <div className="grid md:grid-cols-3 gap-6">
            {posts?.map((post) => (
              <Link
                key={post.id}
                to={`/bai-viet/${post.slug}`}
                className="card overflow-hidden hover:shadow-lift transition-shadow"
              >
                <div className="aspect-16/10">
                  <PlaceholderMedia
                    tone={post.placeholderTone}
                    icon={Newspaper}
                    className="w-full h-full"
                    iconClassName="w-8 h-8"
                  />
                </div>
                <div className="p-5">
                  <div className="text-[11px] font-bold uppercase tracking-wide text-primary">
                    {post.tag}
                  </div>
                  <h3 className="font-display text-lg mt-2 mb-2.5 leading-snug">
                    {post.title}
                  </h3>
                  <div className="text-xs text-muted">
                    {post.readMinutes} phút đọc
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
