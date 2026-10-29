import HeroSection from "./sections/HeroSection";
import CategorySection from "./sections/CategorySection";
import BestSellerSection from "./sections/BestSellerSection";
import AIRecommendationSection from "./sections/AIRecommendationSection";
import ComboSection from "./sections/ComboSection";
import StorySection from "./sections/StorySection";
import PromoPreviewSection from "./sections/PromoPreviewSection";
import BlogPreviewSection from "./sections/BlogPreviewSection";
import TestimonialSection from "./sections/TestimonialSection";

/**
 * HomePage is a pure composition — each section owns its own data
 * fetching (via src/hooks/useAsync + src/api/*.ts) and local UI state.
 * To edit one part of the homepage, open the matching file in ./sections/
 * instead of scrolling through one giant page file.
 */
export default function HomePage() {
  return (
    <div>
      <HeroSection />
      <CategorySection />
      <BestSellerSection />
      <AIRecommendationSection />
      <ComboSection />
      <StorySection />
      <PromoPreviewSection />
      <BlogPreviewSection />
      <TestimonialSection />
    </div>
  );
}
