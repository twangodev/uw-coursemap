declare global {
  namespace App {
    interface Platform {
      env: {
        DB: D1Database;
        SITE_COMMIT?: string;
        DATA_PROJECTION?: string;
        DEPLOYED_AT?: string;
        ASSETS: Fetcher;
      };
      context: ExecutionContext;
    }
  }
}
export {};
