/** Data shared by page loaders and public document representations. */
export interface DocumentContext {
  params: Record<string, string>;
  platform?: App.Platform;
  url: URL;
  setHeaders: (headers: Record<string, string>) => void;
}
