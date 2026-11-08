import HeroSection from "./sections/HeroSection";
import MenuBannerSection from "./sections/MenuBannerSection";
import StorySection from "./sections/StorySection";
import BestSellerSection from "./sections/BestSellerSection";
import RecommendedSection from "./sections/RecommendedSection";
import WhyChooseSection from "./sections/WhyChooseSection";
import PromoPreviewSection from "./sections/PromoPreviewSection";
import CtaSection from "./sections/CtaSection";
import TestimonialSection from "./sections/TestimonialSection";
import BlogPreviewSection from "./sections/BlogPreviewSection";

/**
 * HomePage is a pure composition — each section owns its own data
 * fetching (via src/hooks/useAsync + src/api/*.ts) and local UI state.
 * `.home-classic` (src/index.css) scopes the burgundy + serif theme to this page.
 */
export default function HomePage() {
  return (
    <div className="home-classic">
      <HeroSection />
      <StorySection />
      <MenuBannerSection />
      <RecommendedSection />
      <BestSellerSection />
      <WhyChooseSection />
      <PromoPreviewSection />
      <CtaSection />
      <TestimonialSection />
      <BlogPreviewSection />
    </div>
  );
}
