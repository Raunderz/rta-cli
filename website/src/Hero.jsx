import { useEffect, useRef } from 'preact/hooks';
import { LandscapeHero } from './icons';
import { Link } from 'wouter';

export const TerminalDemo = () => {
  const terminalRef = useRef(null);
  const infoRef = useRef(null);

  useEffect(() => {
    let isRunning = true;
    let timeoutIds = [];

    const sleep = (ms) => new Promise((r) => {
      const id = setTimeout(r, ms);
      timeoutIds.push(id);
    });

    const scrollToBottom = () => {
      if (terminalRef.current) {
        terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
      }
    };

    const el = (tag, styleStr, content) => {
      const e = document.createElement(tag);
      if (styleStr) e.style.cssText = styleStr;
      if (content) {
        if (typeof content === 'string') e.textContent = content;
        else e.appendChild(content);
      }
      return e;
    };

    const addInfoLine = async (label, value, delay = 0) => {
      await sleep(delay);
      if (!isRunning || !infoRef.current) return;
      const line = el('div', "display: flex; justify-content: space-between; margin-bottom: 0.2rem; font-size: 9px; line-height: 1.5;");
      line.appendChild(el('span', "color: var(--text-muted);", label));
      line.appendChild(el('span', "color: var(--primary); font-weight: 500;", value));
      infoRef.current.appendChild(line);
    };

    const typeCmd = async (text, speed = 30) => {
      if (!isRunning || !terminalRef.current) return;
      const span = el('span', "color: var(--primary);");
      terminalRef.current.lastChild.appendChild(span);
      for (let char of text) {
        if (!isRunning) return;
        span.textContent += char;
        scrollToBottom();
        await sleep(speed);
      }
    };

    const showLoader = async (duration = 1800) => {
      if (!isRunning || !terminalRef.current) return;
      const frames = ['-', '\\', '|', '/'];
      let frame = 0;
      const start = Date.now();
      const loaderSpan = el('span', "color: var(--primary); font-size: 10px;");
      terminalRef.current.appendChild(loaderSpan);
      return new Promise((r) => {
        const iv = setInterval(() => {
          if (!isRunning) { clearInterval(iv); r(); return; }
          loaderSpan.textContent = frames[frame % frames.length] + ' Processing...';
          frame++;
          scrollToBottom();
          if (Date.now() - start > duration) {
            clearInterval(iv);
            loaderSpan.remove();
            r();
          }
        }, 80);
        timeoutIds.push(iv);
      });
    };

    const addTool = async (name) => {
      await sleep(400);
      if (!isRunning || !terminalRef.current) return;
      const line = el('div', "color: var(--text-secondary); margin-bottom: 0.3rem; font-size: 10px; display: flex; align-items: center; gap: 0.5rem;");
      line.appendChild(el('span', "color: var(--primary); font-weight: bold;", "[+]"));
      line.appendChild(el('span', "", name));
      terminalRef.current.appendChild(line);
      scrollToBottom();
      await sleep(500);
      if (!isRunning || !terminalRef.current) return;
      terminalRef.current.appendChild(el('div', "color: var(--text-muted); margin-bottom: 0.3rem; font-size: 9px; margin-left: 1.5rem;", "[done]"));
      scrollToBottom();
    };

    const agentMsg = async (msg) => {
      await sleep(600);
      if (!isRunning || !terminalRef.current) return;
      const line = el('div', "color: var(--text-primary); margin-top: 0.4rem; padding: 0.5rem; background: var(--accent-glow); border-left: 2px solid var(--primary); font-size: 10px; line-height: 1.5;");
      terminalRef.current.appendChild(line);
      for (let char of msg) {
        if (!isRunning) return;
        line.textContent += char;
        scrollToBottom();
        await sleep(15);
      }
    };

    const runDemo = async () => {
      if (!isRunning || !infoRef.current || !terminalRef.current) return;
      infoRef.current.innerHTML = '';
      terminalRef.current.innerHTML = '';

      const scenarios = [
        {
          command: 'create a todo app with nextjs and stripe',
          tools: ['read_directory', 'create_file', 'install_package', 'configure_env', 'run_build'],
          message: 'Done! Created a Next.js todo app with Stripe integration and auth setup.'
        },
        {
          command: 'train a simple neural network in c++ for mnist',
          tools: ['create_file', 'configure_compiler', 'optimize_weights', 'run_simulation'],
          message: 'Training complete. Accuracy: 98.4%. Weights saved to model.bin.'
        },
        {
          command: 'generate the rta landing page with vanjs',
          tools: ['analyze_branding', 'scaffold_project', 'generate_components', 'apply_styling'],
          message: 'Website generated! High-performance landing page with terminal animations ready.'
        }
      ];

      const scenario = scenarios[Math.floor(Math.random() * scenarios.length)];

      await addInfoLine('Version', 'v0.6.0', 0);
      await addInfoLine('User', 'test@example.com', 100);
      await addInfoLine('Provider', 'rta', 100);
      await addInfoLine('Model', 'auto', 100);
      await addInfoLine('RAM', '42.5 MB', 100);

      await sleep(400);
      if (!isRunning || !terminalRef.current) return;

      const prompt = el('div', "color: var(--primary); margin-bottom: 0.3rem; font-size: 10px; margin-top: 0.6rem;", "rta >");
      terminalRef.current.appendChild(prompt);
      await typeCmd(scenario.command, 40);
      await showLoader(2000);

      for (const tool of scenario.tools) {
        await addTool(tool);
      }

      await agentMsg(scenario.message);
      await sleep(4000);
      if (isRunning) runDemo();
    };

    runDemo();

    return () => {
      isRunning = false;
      timeoutIds.forEach(id => clearTimeout(id));
    };
  }, []);

  return (
    <div class="hero-visual">
      <div class="terminal-header">
        <div class="terminal-dot"></div>
        <div class="terminal-dot"></div>
        <div class="terminal-dot"></div>
        <span style="font-size: 9px; color: var(--text-muted); margin-left: auto; font-family: var(--font-mono);">rta-terminal-demo</span>
      </div>
      <div style="display: flex; flex-direction: column; height: 100%; padding: var(--space-s); overflow: hidden; gap: 0.8rem;">
        <div class="terminal-info-grid">
          <pre class="terminal-ascii">{` _  .-')   .-') _      ('-.     
( \\( -O ) (  OO) )    ( OO ).-. 
 ,------.  /     '._   / . --. / 
|   /\\'. |'--...__)  | \\-.  \\  
|  /  | |'--.  .--'.-'-'  |  | 
|  |_.' |   |  |    \\| |_.'  | 
|  .  '.'   |  |     |  .-.  | 
|  |\\  \\    |  |     |  | |  | 
 \\'--' '--'   \\'--'     \\'--' \\'--'`}</pre>
          <div ref={infoRef} class="terminal-info-lines"></div>
        </div>
        <div ref={terminalRef} class="terminal-scroll"></div>
      </div>
    </div>
  );
};

export const Hero = () => (
  <section class="hero">
    <LandscapeHero />
    <div class="container" style="width:100%;">
      <div class="hero-grid">
        <div class="hero-content">
          <h1>Code <span class="highlight">anywhere</span>.</h1>
          <p>Your AI coding workspace in your pocket. Build, preview, and iterate on any device — no powerful machine required.</p>
          <div class="hero-actions">
            <Link href="/chat" class="btn btn-primary">Try AI Chat</Link>
            <Link href="/auth" class="btn btn-secondary">Start building</Link>
            <Link href="/releases" class="btn btn-ghost">Download app</Link>
          </div>
        </div>
        <TerminalDemo />
      </div>
    </div>
  </section>
);
