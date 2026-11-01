import * as SecureStore from 'expo-secure-store';

// Android auth: backend returns the session ID as a bearer token in the login
// body (android: true) instead of an HttpOnly cookie (backend/app/api/v1/auth.py).
const SESSION_TOKEN_KEY = 'myfarmai_session_token';
const REFRESH_TOKEN_KEY = 'myfarmai_refresh_token';

export async function getSessionToken(): Promise<string | null> {
  return SecureStore.getItemAsync(SESSION_TOKEN_KEY);
}

export async function setSessionToken(token: string): Promise<void> {
  await SecureStore.setItemAsync(SESSION_TOKEN_KEY, token);
}

export async function getRefreshToken(): Promise<string | null> {
  return SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
}

export async function setRefreshToken(token: string): Promise<void> {
  await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, token);
}

export async function clearSessionTokens(): Promise<void> {
  await SecureStore.deleteItemAsync(SESSION_TOKEN_KEY);
  await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
}
