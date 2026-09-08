declare global {
  namespace App {
    interface Platform {
      env: {
        DB_BLUE: D1Database;
        DB_GREEN: D1Database;
        DATA_SLOT: string;
        SITE_COMMIT?: string;
        DEPLOYED_AT?: string;
        ASSETS: Fetcher;
      };
      context: ExecutionContext;
    }
  }
}
export {};
