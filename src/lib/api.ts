import {PUBLIC_API_URL, PUBLIC_SEARCH_API_URL} from "$env/static/public";

export async function apiFetch(path: string): Promise<Response> {
    return await fetch(`${PUBLIC_API_URL}${path}`);
}

export async function apiQueryFetch(query: string): Promise<Response> {
    return await fetch(`${PUBLIC_SEARCH_API_URL}/query`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({"query": query}),
    });
}