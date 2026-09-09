declare global {
  namespace App {
    interface Platform {
      env: {
        DB_A: D1Database;
        DB_B: D1Database;
        DATA_SLOT: string;
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
