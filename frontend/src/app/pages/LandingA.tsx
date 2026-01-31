/**
 * LANDING PAGE VARIANT A
 * Full-screen immersive video background (Apple product launch style)
 */
import { HeroVariantA } from "../components/HeroVariantA";
import { Features } from "../components/Features";
import { HowItWorks } from "../components/HowItWorks";
import { UseCases } from "../components/UseCases";
import { Pricing } from "../components/Pricing";
import { Testimonials } from "../components/Testimonials";
import { FAQ } from "../components/FAQ";
import { LaunchSection } from "../components/LaunchSection";

export function LandingA() {
  return (
    <main className="min-h-screen bg-black">
      <HeroVariantA />
      <Features />
      <HowItWorks />
      <UseCases />
      <Pricing />
      <Testimonials />
      <FAQ />
      <LaunchSection />
    </main>
  );
}
