import { clearStoredTokens, readStoredTokens, writeStoredTokens } from "./token-storage";
import type { LoginResponse, MobileUser, NotificationPage, RequestPage, ServiceRequest, TokenPair } from "./types";

const configuredOrigin = (process.env.EXPO_PUBLIC_API_BASE_URL ?? "").trim().replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function getApiConfigurationIssue(): string | null {
  if (!configuredOrigin) {
    return "Set EXPO_PUBLIC_API_BASE_URL to the origin of the Auto Aid API to enable sign in.";
  }

  try {
    const url = new URL(configuredOrigin);
    if (!new Set(["http:", "https:"]).has(url.protocol)) {
      return "The API URL must use HTTP or HTTPS.";
    }
    if (url.username || url.password || url.pathname !== "/" || url.search || url.hash) {
      return "Use only the API origin, for example https://api.example.com.";
    }
    if (!__DEV__ && url.protocol !== "https:") {
      return "The API must use HTTPS outside development.";
    }
    return null;
  } catch {
    return "The API URL is invalid. Use an origin such as https://api.example.com.";
  }
}

export function isApiConfigured(): boolean {
  return getApiConfigurationIssue() === null;
}

function apiUrl(path: string): string {
  const issue = getApiConfigurationIssue();
  if (issue) throw new ApiError(issue, 0);

  const origin = new URL(configuredOrigin).origin;
  const url = new URL(path, `${origin}/`);
  if (url.origin !== origin) {
    throw new ApiError("The API returned a pagination link for an unexpected host.", 0);
  }
  return url.toString();
}

async function parseJson(response: Response): Promise<unknown> {
  if (response.status === 204) return null;
  const body = await response.text();
  if (!body) return null;

  try {
    return JSON.parse(body) as unknown;
  } catch {
    return null;
  }
}

function responseMessage(payload: unknown, fallback: string): string {
  if (typeof payload === "object" && payload !== null && "detail" in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}

let refreshInFlight: Promise<boolean> | null = null;

async function refreshSessionOnce(): Promise<boolean> {
  const tokens = await readStoredTokens();
  if (!tokens) return false;

  let response: Response;
  try {
    response = await fetch(apiUrl("/api/v1/auth/refresh/"), {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: tokens.refresh }),
    });
  } catch {
    throw new ApiError("Could not refresh the session. Check your connection and try again.", 0);
  }

  const payload = await parseJson(response);
  if (response.status === 400 || response.status === 401) {
    await clearStoredTokens();
    return false;
  }
  if (!response.ok) {
    throw new ApiError(responseMessage(payload, "Session refresh failed."), response.status);
  }

  const refreshed = payload as Partial<TokenPair> | null;
  if (!refreshed?.access) {
    await clearStoredTokens();
    return false;
  }

  await writeStoredTokens({
    access: refreshed.access,
    refresh: refreshed.refresh ?? tokens.refresh,
  });
  return true;
}

async function refreshSession(): Promise<boolean> {
  if (!refreshInFlight) {
    refreshInFlight = refreshSessionOnce();
  }

  const pending = refreshInFlight;
  try {
    return await pending;
  } finally {
    if (refreshInFlight === pending) refreshInFlight = null;
  }
}

async function performRequest<T>(
  path: string,
  init: RequestInit,
  authenticated: boolean,
  canRefresh: boolean,
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (authenticated) {
    const tokens = await readStoredTokens();
    if (!tokens) throw new ApiError("Your session has ended. Sign in again.", 401);
    headers.set("Authorization", `Bearer ${tokens.access}`);
  }

  let response: Response;
  try {
    response = await fetch(apiUrl(path), { ...init, headers });
  } catch {
    throw new ApiError("Could not reach Auto Aid. Check your connection and API URL.", 0);
  }

  if (response.status === 401 && authenticated) {
    if (canRefresh && (await refreshSession())) {
      return performRequest<T>(path, init, true, false);
    }
    await clearStoredTokens();
    throw new ApiError("Your session has expired. Sign in again.", 401);
  }

  const payload = await parseJson(response);
  if (!response.ok) {
    throw new ApiError(responseMessage(payload, "The request could not be completed."), response.status);
  }
  return payload as T;
}

export async function signIn(username: string, password: string): Promise<MobileUser> {
  const result = await performRequest<LoginResponse>(
    "/api/v1/auth/login/",
    { method: "POST", body: JSON.stringify({ username, password }) },
    false,
    false,
  );

  if (!result?.access || !result?.refresh || !result?.user) {
    throw new ApiError("The API returned an invalid sign-in response.", 502);
  }

  await writeStoredTokens({ access: result.access, refresh: result.refresh });
  return result.user;
}

export function getCurrentUser(): Promise<MobileUser> {
  return performRequest<MobileUser>("/api/v1/me/", {}, true, true);
}

export function getRequestPage(path: string): Promise<RequestPage> {
  return performRequest<RequestPage>(path, {}, true, true);
}

export function getNotificationPage(path: string): Promise<NotificationPage> {
  return performRequest<NotificationPage>(path, {}, true, true);
}

export function getRequest(requestId: number): Promise<ServiceRequest> {
  return performRequest<ServiceRequest>(`/api/v1/requests/${requestId}/`, {}, true, true);
}

async function sendLogout(tokens: TokenPair): Promise<Response> {
  return fetch(apiUrl("/api/v1/auth/logout/"), {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      Authorization: `Bearer ${tokens.access}`,
    },
    body: JSON.stringify({ refresh: tokens.refresh }),
  });
}

export async function signOut(): Promise<void> {
  try {
    let tokens = await readStoredTokens();
    if (!tokens || !isApiConfigured()) return;

    let response: Response;
    try {
      response = await sendLogout(tokens);
    } catch {
      return;
    }

    if (response.status === 401 && (await refreshSession())) {
      tokens = await readStoredTokens();
      if (tokens) {
        try {
          await sendLogout(tokens);
        } catch {
          return;
        }
      }
    }
  } finally {
    await clearStoredTokens();
  }
}
