const fs = require('fs');
const path = require('path');

const src = path.join(__dirname, '..', 'src');
const root = path.join(__dirname, '..');
let pass = 0, fail = 0;

function test(name, fn) {
  try { fn(); pass++; console.log(`  PASS  ${name}`); }
  catch (e) { fail++; console.log(`  FAIL  ${name}: ${e.message}`); }
}

function assert(cond, msg) {
  if (!cond) throw new Error(msg || 'assertion failed');
}

function fileExists(p) {
  return fs.existsSync(path.join(root, p));
}

function readFile(p) {
  return fs.readFileSync(path.join(root, p), 'utf8');
}

// =========================================================================
console.log('\n=== Website Structure Tests ===\n');

test('main.jsx is a thin entry point (< 5 lines)', () => {
  const lines = readFile('main.jsx').split('\n').filter(l => l.trim());
  assert(lines.length <= 5, `main.jsx has ${lines.length} non-empty lines`);
});

test('App.jsx imports ErrorBoundary', () => {
  const app = readFile('src/App.jsx');
  assert(app.includes('ErrorBoundary'), 'App.jsx missing ErrorBoundary import');
});

test('App.jsx uses lazy() for heavy routes', () => {
  const app = readFile('src/App.jsx');
  assert(app.includes('lazy('), 'App.jsx missing lazy() calls');
  assert(app.includes('Suspense'), 'App.jsx missing Suspense');
});

test('App.jsx lazy-loads BlogPage', () => {
  const app = readFile('src/App.jsx');
  assert(app.includes("import('../blog.jsx')"), 'BlogPage not lazy-loaded');
});

test('App.jsx lazy-loads Dashboard', () => {
  const app = readFile('src/App.jsx');
  assert(app.includes("import('../dashboard.jsx')"), 'Dashboard not lazy-loaded');
});

test('App.jsx lazy-loads ChatInterface', () => {
  const app = readFile('src/App.jsx');
  assert(app.includes("import('../chat_interface.jsx')"), 'ChatInterface not lazy-loaded');
});

test('ErrorBoundary component exists', () => {
  assert(fileExists('src/ErrorBoundary.jsx'), 'ErrorBoundary.jsx not found');
});

test('ErrorBoundary extends Component', () => {
  const eb = readFile('src/ErrorBoundary.jsx');
  assert(eb.includes('extends Component'), 'ErrorBoundary must extend Component');
});

test('ErrorBoundary has getDerivedStateFromError', () => {
  const eb = readFile('src/ErrorBoundary.jsx');
  assert(eb.includes('getDerivedStateFromError'), 'Missing getDerivedStateFromError');
});

test('ErrorBoundary renders fallback UI on error', () => {
  const eb = readFile('src/ErrorBoundary.jsx');
  assert(eb.includes('Something went wrong'), 'Missing fallback error message');
});

// =========================================================================
console.log('\n=== useHead Tests ===\n');

test('useHead hook exists', () => {
  assert(fileExists('src/useHead.js'), 'useHead.js not found');
});

test('useHead updates document.title', () => {
  const hook = readFile('src/useHead.js');
  assert(hook.includes('document.title'), 'useHead must set document.title');
});

test('useHead accepts title and description', () => {
  const hook = readFile('src/useHead.js');
  assert(hook.includes('title'), 'useHead must accept title');
  assert(hook.includes('description'), 'useHead must accept description');
});

// =========================================================================
console.log('\n=== Blog from Markdown Tests ===\n');

test('blog/index.json exists', () => {
  assert(fileExists('public/blog/index.json'), 'blog/index.json not found');
});

test('blog/index.json is valid JSON with articles', () => {
  const index = JSON.parse(readFile('public/blog/index.json'));
  assert(Array.isArray(index), 'index.json must be an array');
  assert(index.length >= 10, `Expected >= 10 articles, got ${index.length}`);
});

test('every article in index has required fields', () => {
  const index = JSON.parse(readFile('public/blog/index.json'));
  for (const a of index) {
    assert(a.slug, `Article missing slug: ${JSON.stringify(a)}`);
    assert(a.title, `Article missing title: ${a.slug}`);
    assert(a.date, `Article missing date: ${a.slug}`);
    assert(a.readTime, `Article missing readTime: ${a.slug}`);
    assert(a.excerpt, `Article missing excerpt: ${a.slug}`);
    assert(Array.isArray(a.tags), `Article tags not array: ${a.slug}`);
  }
});

test('every article has a corresponding .md file', () => {
  const index = JSON.parse(readFile('public/blog/index.json'));
  for (const a of index) {
    assert(fileExists(`public/blog/${a.slug}.md`), `Missing public/blog/${a.slug}.md`);
  }
});

test('markdown files have frontmatter', () => {
  const index = JSON.parse(readFile('public/blog/index.json'));
  for (const a of index) {
    const content = readFile(`public/blog/${a.slug}.md`);
    assert(content.startsWith('---'), `${a.slug}.md missing frontmatter`);
    assert(content.includes('---', 3), `${a.slug}.md frontmatter not closed`);
  }
});

test('blog.jsx fetches from /blog/index.json', () => {
  const blog = readFile('blog.jsx');
  assert(blog.includes('/blog/index.json'), 'blog.jsx must fetch index.json');
});

test('blog.jsx fetches individual .md files', () => {
  const blog = readFile('blog.jsx');
  assert(blog.includes('/blog/'), 'blog.jsx must fetch .md files');
});

test('blog.jsx no longer has hardcoded article bodies', () => {
  const blog = readFile('blog.jsx');
  // Should not contain the old inline markdown
  assert(!blog.includes('Two weeks ago, we wrote about'), 'blog.jsx still has hardcoded body content');
  assert(!blog.includes('body: `'), 'blog.jsx still has inline body templates');
});

// =========================================================================
console.log('\n=== useHead in Pages Tests ===\n');

const pagesWithHead = [
  ['src/pages.jsx', 'PricingPage', 'Pricing'],
  ['src/pages.jsx', 'RoadmapPage', 'Roadmap'],
  ['src/AuthPage.jsx', 'AuthPage', 'Account'],
  ['src/ReleasesPage.jsx', 'ReleasesPage', 'Releases'],
  ['src/ApiPage.jsx', 'ApiPage', 'API'],
  ['src/Home.jsx', 'Home', 'Code Anywhere'],
];

for (const [file, component, expectedTitle] of pagesWithHead) {
  test(`${component} uses useHead with "${expectedTitle}"`, () => {
    const content = readFile(file);
    assert(content.includes('useHead'), `${file} missing useHead import/call`);
    assert(content.includes(`"${expectedTitle}"`), `${file} missing title "${expectedTitle}"`);
  });
}

// =========================================================================
console.log('\n=== Lazy Loading Boundary Tests ===\n');

test('Navbar is NOT lazy-loaded (always visible)', () => {
  const app = readFile('src/App.jsx');
  assert(!app.includes("import('./Navbar')") || !app.includes('lazy'), 'Navbar should be eagerly imported');
});

test('Home is NOT lazy-loaded (above the fold)', () => {
  const app = readFile('src/App.jsx');
  assert(!app.includes("import('./Home')") || !app.includes('lazy'), 'Home should be eagerly imported');
});

test('Footer components are NOT lazy-loaded', () => {
  const app = readFile('src/App.jsx');
  assert(!app.includes("import('./Footer')") || !app.includes('lazy'), 'Footer should be eagerly imported');
});

// =========================================================================
console.log(`\n=== Results: ${pass} passed, ${fail} failed ===\n`);
process.exit(fail > 0 ? 1 : 0);
