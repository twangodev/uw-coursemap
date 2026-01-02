import { createApiClient } from "$lib/api";
import { formatTimeAgo } from "$lib/utils/timeago";

export const load = async ({ fetch }) => {
  const api = createApiClient(fetch);

  const { data, error } = await api.GET("/update");

  if (error || !data?.updated_on) {
    console.error("Failed to fetch update time:", error);
    return {
      lastSynced: "unknown",
    };
  }

  const updatedOn = new Date(data.updated_on);
  const lastSynced = formatTimeAgo(updatedOn);

  return {
    lastSynced,
  };
};