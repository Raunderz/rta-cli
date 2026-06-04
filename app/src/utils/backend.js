const PRIMARY_URL = 'https://schallten-a2xtbb49ws.hf.space';
const BACKUP_URL = 'https://rta-tb0k.onrender.com';
const FAILOVER_TIMEOUT = 5000;

let _resolvedUrl = null;

export async function resolveBackendUrl() {
  if (_resolvedUrl) return _resolvedUrl;

  const urls = [BACKUP_URL, PRIMARY_URL];
  for (const url of urls) {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), FAILOVER_TIMEOUT);
      const res = await fetch(`${url}/health`, {
        method: 'GET',
        signal: controller.signal,
      });
      clearTimeout(timer);
      if (res.ok) {
        _resolvedUrl = url;
        return url;
      }
    } catch {
      continue;
    }
  }

  _resolvedUrl = PRIMARY_URL;
  return PRIMARY_URL;
}

export function getBackendUrlSync() {
  return _resolvedUrl || PRIMARY_URL;
}
