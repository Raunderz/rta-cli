/**
 * @typedef {{ role: string, content: string }} Message
 * @typedef {{ type: string, content: any }} StreamEvent
 */

const SERVER_URL = 'https://rta-tb0k.onrender.com';

class AgentSidecar {
  constructor() {
    /** @type {string | null} */
    this.apiKey = null;
    /** @type {AbortController | null} */
    this._abort = null;
  }

  /**
   * Set the API key for authentication.
   * @param {string} key
   */
  setApiKey(key) {
    this.apiKey = key;
  }

  /**
   * Send a prompt to the backend and stream the response via SSE.
   *
   * @param {string} prompt
   * @param {object} options
   * @param {Message[]} [options.messages] - full message history (optional, builds from prompt)
   * @param {string} [options.workspace] - workspace path for telemetry
   * @param {(event: StreamEvent) => void} onEvent - called for each SSE event
   * @returns {Promise<string>} - resolves with the full assistant text
   */
  async ask(prompt, { messages, workspace } = {}, onEvent) {
    if (!this.apiKey) {
      throw new Error('No API key. Run: rta login');
    }

    // Build messages array
    const msgs = messages || [{ role: 'user', content: prompt }];

    // Abort any in-flight request
    this._abort?.abort();
    this._abort = new AbortController();

    const response = await fetch(`${SERVER_URL}/v1/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-KEY': this.apiKey,
      },
      body: JSON.stringify({
        messages: msgs,
        model: 'auto',
        provider: 'auto',
        stream: true,
        workspace_path: workspace || '',
        max_tokens: 2000,
      }),
      signal: this._abort.signal,
    });

    if (!response.ok) {
      const text = await response.text().catch(() => '');
      throw new Error(`API error ${response.status}: ${text.slice(0, 200)}`);
    }

    // Parse SSE stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullText = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith('data: ')) continue;

        const dataStr = trimmed.slice(6).trim();
        if (!dataStr || dataStr === '[DONE]') continue;

        try {
          /** @type {StreamEvent} */
          const event = JSON.parse(dataStr);

          if (event.type === 'text') {
            fullText += event.content || '';
          }

          if (onEvent) onEvent(event);
        } catch {
          // skip malformed JSON
        }
      }
    }

    return fullText;
  }

  /**
   * Cancel the current request.
   */
  cancel() {
    this._abort?.abort();
    this._abort = null;
  }

  /**
   * Check if a request is in progress.
   * @returns {boolean}
   */
  isAlive() {
    return this._abort !== null;
  }

  /**
   * No-op for compatibility. No process to stop.
   * @returns {Promise<void>}
   */
  stop() {
    this.cancel();
    return Promise.resolve();
  }
}

module.exports = { AgentSidecar, SERVER_URL };
