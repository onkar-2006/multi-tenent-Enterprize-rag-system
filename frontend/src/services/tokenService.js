import { API_BASE_URL } from '../config/portals';

let cachedTokens = null;

export async function fetchPortalTokens() {
  if (cachedTokens) return cachedTokens;
  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/tokens`);
    if (!res.ok) throw new Error('Failed to fetch tokens');
    const data = await res.json();
    cachedTokens = data;
    return data;
  } catch (err) {
    console.error('Error fetching portal tokens:', err);
    // Fallback token structure if offline/loading
    return null;
  }
}

export function parseJwt(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}
