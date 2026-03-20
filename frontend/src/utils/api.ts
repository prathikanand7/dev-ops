export function decodeApiBody<T>(raw: unknown): T {
  if (typeof raw === 'string') {
    try { return JSON.parse(raw) as T; } catch { throw new Error(`Non-JSON: ${raw}`); }
  }
  return raw as T;
}

export function deriveS3Uri(downloadUrl: string): string | null {
  try {
    const parsed = new URL(downloadUrl);
    const host = parsed.hostname;
    const path = decodeURIComponent(parsed.pathname).replace(/^\/+/, '');
    if (!path) return null;

    const hostParts = host.split('.');
    if (hostParts.length > 0 && hostParts[0] && hostParts[0] !== 's3') {
      return `s3://${hostParts[0]}/${path}`;
    }

    const [bucket, ...rest] = path.split('/');
    if (!bucket || rest.length === 0) return null;
    return `s3://${bucket}/${rest.join('/')}`;
  } catch {
    return null;
  }
}
