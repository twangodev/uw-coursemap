export function modelPublisher(model?: string | null): string | null {
  return model?.match(/^([a-z0-9][\w-]*)\/[^/]+$/i)?.[1].toLowerCase() || null;
}
export interface ModelPublisher { name: string; avatar: string | null }
const publishers = new Map<string, Promise<ModelPublisher | null>>();
/** Fetch public HF publisher metadata only when a disclaimer is opened. */
export function resolveModelPublisher(model?: string | null): Promise<ModelPublisher | null> {
  const owner = modelPublisher(model);
  if (!owner) return Promise.resolve(null);
  let pending = publishers.get(owner);
  if (!pending) {
    pending = (async () => {
      const options = { credentials: 'omit' as const, signal: AbortSignal.timeout(5000) };
      let response = await fetch(`https://huggingface.co/api/organizations/${encodeURIComponent(owner)}/overview`, options);
      if (response.status === 404) response = await fetch(`https://huggingface.co/api/users/${encodeURIComponent(owner)}/overview`, options);
      if (!response.ok) throw new Error('Publisher unavailable');
      const payload: unknown = await response.json();
      if (!payload || typeof payload !== "object") throw new Error("Invalid publisher metadata");
      const data = payload as Record<string, unknown>;
      let avatar: string | null = null;
      if (typeof data.avatarUrl === 'string') {
        const url = new URL(data.avatarUrl);
        if (url.protocol === 'https:' && ['cdn-avatars.huggingface.co', 'huggingface.co'].includes(url.hostname)) avatar = url.href;
      }
      return { name: typeof data.fullname === 'string' ? data.fullname : owner, avatar };
    })().catch(() => { publishers.delete(owner); return null; });
    if (publishers.size >= 50) publishers.delete(publishers.keys().next().value!);
    publishers.set(owner, pending);
  }
  return pending;
}
