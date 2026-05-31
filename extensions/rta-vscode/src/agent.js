const { spawn } = require('child_process');

class AgentSidecar {
  constructor() {
    this.process = null;
    this.requestId = 0;
    this.pending = new Map();
    this.buffer = '';
  }

  async start() {
    // TODO: detect rta binary path (bundled, PATH, or setting)
    const binary = 'rta';
    // TODO: spawn with --json-rpc flag (needs CLI support)
    this.process = spawn(binary, [], {
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    this.process.stdout.on('data', (chunk) => {
      this.buffer += chunk.toString();
      // TODO: parse JSON-RPC lines, resolve pending promises
    });

    this.process.on('exit', (code) => {
      console.log(`RTA agent exited (${code})`);
      // TODO: auto-restart with backoff
    });
  }

  async call(method, params) {
    const id = ++this.requestId;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      const msg = JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n';
      this.process.stdin.write(msg);
    });
  }

  async stream(method, params, onData) {
    // TODO: streaming variant — read ndjson lines, call onData per line
  }

  async stop() {
    if (this.process) {
      this.process.kill();
      this.process = null;
    }
  }
}

module.exports = { AgentSidecar };
