import { apiClient } from "./client";
import { mapPost } from "./mappers";
import type { BlogPost } from "@/types";

export async function getBlogPosts(): Promise<BlogPost[]> {
  const { data } = await apiClient.get("/posts/");
  return (Array.isArray(data) ? data : data.results).map(mapPost);
}

export async function getBlogPostBySlug(slug: string): Promise<BlogPost | undefined> {
  try { const { data } = await apiClient.get(`/posts/${slug}/`); return mapPost(data); }
  catch (error: any) { if (error.response?.status === 404) return undefined; throw error; }
}

export async function getOtherBlogPosts(excludeId: string, limit = 2): Promise<BlogPost[]> {
  const posts = await getBlogPosts();
  return posts.filter((post) => post.id !== excludeId).slice(0, limit);
}
