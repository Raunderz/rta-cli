import { render, h } from 'preact';
import { useState } from 'preact/hooks';
import { lazy, Suspense } from 'preact/compat';
import { Router, Route, useRoute, Switch } from 'wouter';
import { Analytics } from "@vercel/analytics/react";

import Navbar from './Navbar';
import { Home } from './Home';
import { PricingPage, StatusPage, LegalPage, PrivacyPage, RoadmapPage } from './pages';
import { AppFooter, NotFoundPage, ServiceNotice, CookieBanner } from './Footer';
import ErrorBoundary from './ErrorBoundary';

const AuthPage = lazy(() => import('./AuthPage').then(m => ({ default: m.AuthPage })));
const ReleasesPage = lazy(() => import('./ReleasesPage').then(m => ({ default: m.ReleasesPage })));
const ApiPage = lazy(() => import('./ApiPage').then(m => ({ default: m.ApiPage })));
const BlogPage = lazy(() => import('../blog.jsx').then(m => ({ default: m.BlogPage })));
const DocsPage = lazy(() => import('../docs.jsx').then(m => ({ default: m.DocsPage })));
const Dashboard = lazy(() => import('../dashboard.jsx'));
const ChatInterface = lazy(() => import('../chat_interface.jsx'));

const Loading = () => (
  <div style="min-height: 60vh; display: flex; align-items: center; justify-content: center;">
    <div style="width: 20px; height: 20px; border: 2px solid var(--border); border-top-color: var(--primary); border-radius: 50%; animation: spin 0.6s linear infinite;" />
    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
  </div>
);

const App = () => {
  const [match] = useRoute("/chat");
  if (match) return <ErrorBoundary><Suspense fallback={<Loading />}><ChatInterface /></Suspense></ErrorBoundary>;

  return (
    <div class="app-container">
      <Navbar />
      <main class="main-content">
        <ErrorBoundary>
          <Suspense fallback={<Loading />}>
            <Router>
              <Switch>
                <Route path="/" component={Home} />
                <Route path="/pricing" component={PricingPage} />
                <Route path="/roadmap" component={RoadmapPage} />
                <Route path="/status" component={StatusPage} />
                <Route path="/releases" component={ReleasesPage} />
                <Route path="/auth" component={AuthPage} />
                <Route path="/legal" component={LegalPage} />
                <Route path="/privacy" component={PrivacyPage} />
                <Route path="/blog" component={BlogPage} />
                <Route path="/blog/:slug" component={BlogPage} />
                <Route path="/docs" component={DocsPage} />
                <Route path="/api" component={ApiPage} />
                <Route path="/dashboard" component={Dashboard} />
                <Route component={NotFoundPage} />
              </Switch>
            </Router>
          </Suspense>
        </ErrorBoundary>
      </main>
      <ServiceNotice />
      <CookieBanner />
      <AppFooter />
      <Analytics />
    </div>
  );
};

render(<App />, document.body);
