import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { Link, useLocation } from 'wouter';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { useHead } from './src/useHead';

const API_BASE = import.meta.env.VITE_BACKEND_URL || "https://rta-tb0k.onrender.com";

export const BlogPage = ({ params }) => {
  const [, setLocation] = useLocation();
  const [articles, setArticles] = useState([]);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/blog/index.json')
      .then(r => r.json())
      .then(data => {
        setArticles(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (params?.slug && articles.length > 0) {
      const meta = articles.find(a => a.slug === params.slug);
      if (meta) {
        fetch(`/blog/${meta.slug}.md`)
          .then(r => r.text())
          .then(text => {
            // Strip frontmatter
            const body = text.replace(/^---[\s\S]*?---\n/, '');
            setSelectedArticle({ ...meta, body });
            window.scrollTo(0, 0);
          })
          .catch(() => setSelectedArticle(null));
      } else {
        setSelectedArticle(null);
      }
    } else {
      setSelectedArticle(null);
    }
  }, [params?.slug, articles]);

  useHead(selectedArticle
    ? { title: selectedArticle.title, description: selectedArticle.excerpt }
    : { title: "Blog", description: "Technical blog posts from the Rta team." }
  );

  if (loading) {
    return (
      <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px;">
        <div class="section-header">
          <h2>Transmissions</h2>
          <p class="mono">Technical Blog</p>
        </div>
        <p style="text-align: center; color: var(--text-muted);">Loading...</p>
      </div>
    );
  }

  if (selectedArticle) {
    const htmlContent = marked.parse(selectedArticle.body);

    return (
      <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px; max-width: 800px;">
        <div style="margin-bottom: 2rem;">
          <Link href="/blog" class="nav-link" style="font-family: var(--font-mono); font-size: 0.75rem;">&larr; Back to Blog</Link>
        </div>
        <div style="display: flex; gap: 0.5rem; margin-bottom: 1.5rem; flex-wrap: wrap;">
          {selectedArticle.tags.map(tag => (
            <span class="mono" style="font-size: 0.6rem; padding: 4px 10px; border: 1px solid var(--border); color: var(--text-muted);" key={tag}>{tag}</span>
          ))}
        </div>
        <h2 style="margin-bottom: 1rem; font-size: clamp(2.2rem, 6vw, 3.5rem); line-height: 1; font-family: var(--font-display);">{selectedArticle.title}</h2>
        <div style="display: flex; gap: 2rem; margin-bottom: 3rem; border-bottom: 1px solid var(--border); padding-bottom: 1.5rem; flex-wrap: wrap;">
          <span class="mono" style="color: var(--text-secondary); font-size: 0.8rem;">{selectedArticle.date}</span>
          <span class="mono" style="color: var(--text-secondary); font-size: 0.8rem;">{selectedArticle.readTime}</span>
        </div>
        <div class="markdown-body" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(htmlContent) }} />
      </div>
    );
  }

  return (
    <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px;">
      <div class="section-header">
        <h2>Transmissions</h2>
        <p class="mono">Technical Blog</p>
      </div>
      <div style="display: flex; flex-direction: column; gap: 2rem; max-width: 800px; margin: 0 auto;">
        {articles.map(article => (
          <div class="feature-card" style="cursor: pointer;" onClick={() => setLocation(`/blog/${article.slug}`)} key={article.slug}>
            <div style="display: flex; gap: 0.5rem; margin-bottom: 1.2rem; flex-wrap: wrap;">
              {article.tags.map(tag => (
                <span class="mono" style="font-size: 0.6rem; padding: 4px 10px; border: 1px solid var(--border); color: var(--text-muted);" key={tag}>{tag}</span>
              ))}
            </div>
            <h3 style="font-size: clamp(1.3rem, 4vw, 1.6rem); margin-bottom: 1rem; font-family: var(--font-display);">{article.title}</h3>
            <p style="margin-bottom: 2rem; color: var(--text-secondary);">{article.excerpt}</p>
            <div style="display: flex; justify-content: space-between; border-top: 1px solid var(--border); padding-top: 1.5rem; gap: 1rem; flex-wrap: wrap;">
              <span class="mono" style="font-size: 0.65rem; color: var(--text-muted);">{article.date}</span>
              <span class="mono" style="font-size: 0.65rem; color: var(--text-muted);">{article.readTime}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
