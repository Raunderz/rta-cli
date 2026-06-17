import { LeafIcon, ZapIcon, CloudIcon } from './icons';
import { Hero } from './Hero';
import { useHead } from './useHead';

const FeaturesSection = () => {
  const features = [
    { icon: CloudIcon, title: "Freedom to roam", desc: "Code from a hillside or a cafe. Your entire dev environment lives in the cloud, ready when you are." },
    { icon: ZapIcon, title: "Your AI partner", desc: "Describe your idea in plain language and watch it become real code in minutes. No boilerplate, just results." },
    { icon: LeafIcon, title: "Seamless transition", desc: "Start on your phone, finish on your laptop. Perfect sync across all your devices, zero friction." }
  ];

  return (
    <section class="features container">
      <div class="section-header">
        <h2>Mobility</h2>
        <p>Unbound creativity for modern makers.</p>
      </div>
      <div class="features-grid">
        {features.map((f, i) => {
          const Icon = f.icon;
          return (
            <div class="feature-card" key={i}>
              <div class="feature-icon">
                <Icon size={22} />
              </div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
};

export const Home = () => {
  useHead({ title: "Code Anywhere", description: "Your AI coding workspace in your pocket. Build, preview, and iterate on any device." });
  return (
    <div>
      <Hero />
      <FeaturesSection />
    </div>
  );
};
