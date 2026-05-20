import { setAuthToken } from "./api/client";

const TOKEN_KEY = "bbp_admin_token";

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function saveToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
  setAuthToken(token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  setAuthToken(null);
}

export function bootstrapAuth(): void {
  const token = getStoredToken();
  setAuthToken(token);
}
