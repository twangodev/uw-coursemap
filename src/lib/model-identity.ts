/** Resolve model family separately from the distributor of a quantized checkpoint. */
export function modelFamily(model?: string | null): 'qwen' | null {
  return model && /(?:^|[/_-])qwen(?:\d|[-_]|$)/i.test(model) ? 'qwen' : null;
}
