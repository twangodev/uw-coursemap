import { env } from "$env/dynamic/public";
import { format } from "timeago.js";

const PUBLIC_API_URL = env.PUBLIC_API_URL;

export const load = async ({ fetch }) => {
  try {
    const response = await fetch(`${PUBLIC_API_URL}/update.json`);
    if (!response.ok) {
      console.error(`Failed to fetch update info: ${response.statusText}`);
      return {
        lastSynced: "unknown"
      };
    }
    
    const data = await response.json();
    const updatedOn = new Date(data.updated_on);
    const lastSynced = format(updatedOn);
    
    return {
      lastSynced
    };
  } catch (error) {
    console.error("Failed to fetch update time:", error);
    return {
      lastSynced: "unknown"
    };
  }
};