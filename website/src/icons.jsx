export const LeafIcon = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <path d="M11 20A7 7 0 0 1 9.8 6.9C15.5 4.9 17 3.5 19 2c1 2 2 4.5 2 8 0 5.5-4.78 10-10 10Z" />
    <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
  </svg>
);

export const ZapIcon = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
);

export const CloudIcon = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z" />
  </svg>
);

export const LandscapeHero = () => (
  <div class="landscape-hero">
    <svg viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice" fill="none" xmlns="http://www.w3.org/2000/svg">
      {[180, 400, 600, 900, 1100, 1300].map((x, i) => (
        <circle key={i} cx={x} cy={250 + i * 40} r={2.5} fill="#FBBF24" opacity="0.3">
          <animate attributeName="cy" values={`${250 + i * 40};${240 + i * 40};${250 + i * 40}`} dur={`${3 + i}s`} repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.2;0.5;0.2" dur={`${4 + i}s`} repeatCount="indefinite" />
        </circle>
      ))}
    </svg>
  </div>
);
