/**
 * LANDING PAGE VARIANT B
 * Split layout with video in device frame (Stripe/Linear style)
 */
import { HeroVariantB } from "../components/HeroVariantB";
import { Features } from "../components/Features";
import { HowItWorks } from "../components/HowItWorks";
import { UseCases } from "../components/UseCases";
import { Pricing } from "../components/Pricing";
import { Testimonials } from "../components/Testimonials";
import { FAQ } from "../components/FAQ";
import { LaunchSection } from "../components/LaunchSection";

export function LandingB() {
  return (
    <main className="min-h-screen bg-black">
      <HeroVariantB />
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
