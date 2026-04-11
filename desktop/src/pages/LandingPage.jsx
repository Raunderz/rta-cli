import { h } from 'preact';
import backgroundImage from '../assets/background.png';
import iconImage from '../assets/icon.png';

export function LandingPage() {
  return (
    <div className="app-container min-h-screen flex items-center justify-center p-4">
      <div className="glass-panel w-full max-w-2xl p-12 md:p-16 text-center">
        <div className="animate-fade-in">
          <img 
            src={iconImage} 
            alt="RTA Logo" 
            className="w-24 h-24 mx-auto mb-8 drop-shadow-2xl"
          />
        </div>
        
        <h1 className="animate-fade-in text-6xl md:text-7xl font-extrabold text-white mb-4 tracking-widest">
          RTA
        </h1>
        
        <div className="animate-fade-in-delay">
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className="h-px w-12 bg-gradient-to-r from-transparent via-white/40 to-transparent"></div>
            <span className="text-white/60 text-lg font-medium uppercase tracking-wider">Coming Soon</span>
            <div className="h-px w-12 bg-gradient-to-r from-transparent via-white/40 to-transparent"></div>
          </div>
        </div>
        
        <p className="animate-fade-in-delay-2 text-white/50 text-lg max-w-md mx-auto leading-relaxed">
          We're crafting something extraordinary. Stay tuned for the launch.
        </p>
        
        <div className="animate-fade-in-delay-2 mt-10 flex justify-center gap-4">
          <div className="glass-card px-6 py-3">
            <span className="text-white/40 text-sm">Get notified when we launch</span>
          </div>
        </div>
      </div>
    </div>
  );
}
