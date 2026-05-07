import { h } from 'preact';
import { useState } from 'preact/hooks';
import { marked } from 'marked';

export const BlogPage = () => {
  const articles = [
    {
      slug: "why-built-rta",
      title: "Why We Built Rta",
      date: "May 7, 2026",
      readTime: "4 min read",
      excerpt: "Understanding the purpose and motivation behind Rta: A mobile-first, AI-assisted code editor.",
      tags: ["Product", "Vision"],
      commit: "initial",
      body: `
# Why We Built Rta

Rta is being built to address the difficulty of mobile-based development workflows, especially those relying on tools like Termux. While powerful, such tools often require manual setup, dependency management, and technical knowledge that can be a barrier for many users.

## Instant-Use Environment

Rta aims to simplify this experience by providing an instant-use environment for:
* Quick code edits
* Emergency bug fixes
* Viewing and understanding repositories on the go
* Lightweight development tasks without setup overhead

## Core Integration

It combines a lightweight code editor, Git integration, and AI assistance into a single mobile application. It is designed for developers who need fast access to code and intelligent support without setting up a full development environment. We want to bridge the gap between heavy desktop IDEs and completely unoptimized mobile experiences.
`
    },
    {
      slug: "cli-agent-architecture",
      title: "Building the RTA CLI Agent",
      date: "May 6, 2026",
      readTime: "6 min read",
      excerpt: "How we implemented project auto-discovery, context persistence, and parallel tool execution.",
      tags: ["CLI", "Python", "Architecture"],
      commit: "1cc10cb",
      body: `
# Rta CLI Agent Architecture

The CLI component is the foundation of Rta. We designed it to be highly context-aware without requiring backend modifications.

## Core Intelligence

We implemented project auto-discovery by scanning the workspace on startup. The CLI detects:
- **Language/Framework**: Reading \`pyproject.toml\`, \`package.json\`, \`Cargo.toml\`, etc.
- **Test Frameworks**: Identifying \`pytest\`, \`vitest\`, \`cargo test\`.
- **Linter Configs**: Checking for \`.eslintrc\`, \`ruff.toml\`.

This allows the agent to automatically deduce the correct commands when a user says "run tests" or "lint the project".

## Parallel Tool Execution

To speed up operations, we implemented a dependency graph for tool execution. If multiple tool calls are independent (e.g., \`get_files_info\` and \`list_directory\`), they execute concurrently. Dependent tools (e.g., \`grep_search\` followed by \`edit_file\`) execute sequentially.
`
    }
  ];

  const [selectedArticle, setSelectedArticle] = useState(null);

  if (selectedArticle) {
    const htmlContent = marked(selectedArticle.body);

    return (
      <div class="container" style="padding-top: 120px; padding-bottom: 80px; max-width: 800px;">
        <div style="margin-bottom: 2rem;">
          <a href="#" class="nav-link" onClick={(e) => { e.preventDefault(); setSelectedArticle(null); }}>← Back to Blog</a>
        </div>
        <div style="display: flex; gap: 0.5rem; margin-bottom: 1.5rem;">
          {selectedArticle.tags.map(tag => (
            <span class="mono" style="font-size: 11px; padding: 4px 10px; border: 1px solid var(--border-color); color: var(--text-muted);">{tag}</span>
          ))}
        </div>
        <h2 style="margin-bottom: 1rem; font-size: 3rem;">{selectedArticle.title}</h2>
        <div style="display: flex; gap: 2rem; margin-bottom: 3rem; border-bottom: 1px solid var(--border-color); padding-bottom: 1.5rem;">
          <span class="mono" style="color: var(--text-muted); font-size: 14px;">{selectedArticle.date}</span>
          <span class="mono" style="color: var(--text-muted); font-size: 14px;">{selectedArticle.readTime}</span>
        </div>
        <div class="markdown-body" dangerouslySetInnerHTML={{ __html: htmlContent }} />
      </div>
    );
  }

  return (
    <div class="container" style="padding-top: 120px; padding-bottom: 80px;">
      <div class="section-header">
        <h2>TRANSMISSIONS</h2>
        <p class="mono">TECHNICAL BLOG</p>
      </div>
      <div style="display: flex; flex-direction: column; gap: 2rem; max-width: 800px; margin: 0 auto;">
        {articles.map(article => (
          <div class="feature-card" style="cursor: pointer;" onClick={() => { setSelectedArticle(article); window.scrollTo(0,0); }}>
            <div style="display: flex; gap: 0.5rem; margin-bottom: 1.2rem;">
              {article.tags.map(tag => (
                <span class="mono" style="font-size: 11px; padding: 4px 10px; border: 1px solid var(--border-color); color: var(--text-muted);">{tag}</span>
              ))}
            </div>
            <h3 style="font-size: 1.8rem; margin-bottom: 1rem;">{article.title}</h3>
            <p style="margin-bottom: 2rem;">{article.excerpt}</p>
            <div style="display: flex; justify-content: space-between; border-top: 1px solid var(--border-color); padding-top: 1.5rem;">
              <span class="mono" style="font-size: 12px; color: var(--text-muted);">{article.date}</span>
              <span class="mono" style="font-size: 12px; color: var(--text-muted);">{article.readTime}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
