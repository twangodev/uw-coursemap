import {PUBLIC_API_URL} from "$env/static/public";

export async function apiFetch(path: string): Promise<Response> {
    return await fetch(`${PUBLIC_API_URL}${path}`);
}