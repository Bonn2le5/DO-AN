import { apiClient } from "./client";
import { mapBaiViet } from "./mappers";
import type { BaiVietBlog } from "@/types";

export async function getBlogPosts(): Promise<BaiVietBlog[]> {
  const { data } = await apiClient.get("/posts/");
  return (Array.isArray(data) ? data : data.results).map(mapBaiViet);
}

export async function getBlogPostBySlug(slug: string): Promise<BaiVietBlog | undefined> {
  try { const { data } = await apiClient.get(`/posts/${slug}/`); return mapBaiViet(data); }
  catch (error: any) { if (error.response?.status === 404) return undefined; throw error; }
}

export async function getOtherBlogPosts(excludeId: string, limit = 2): Promise<BaiVietBlog[]> {
  const posts = await getBlogPosts();
  return posts.filter((post) => post.id !== excludeId).slice(0, limit);
}
