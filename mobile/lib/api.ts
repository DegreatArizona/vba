import { clearStoredTokens, readStoredTokens, writeStoredTokens } from "./token-storage";
import { deleteStoredPushToken, readStoredPushToken } from "./push-token-storage";
import type {
  LoginResponse,
  ManagerMechanicPage,
  ManagerQueuePage,
  MechanicRequestAction,
  MobileNotification,
  MobileRegistrationInput,
  MobileRegistrationResponse,
  MobileUser,
  NotificationPage,
  RequestCreateInput,
  RequestPage,
  ServiceRequest,
  TokenPair,
} from "./types";

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
  if (typeof payload === "object" && payload !== null) {
    if ("detail" in payload) {
      const detail = (payload as { detail?: unknown }).detail;
      if (typeof detail === "string") return detail;
    }
    for (const [field, errors] of Object.entries(payload)) {
      if (typeof errors === "string") return `${field}: ${errors}`;
      if (Array.isArray(errors)) {
        const message = errors.find((item): item is string => typeof item === "string");
        if (message) return `${field}: ${message}`;
      }
    }
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

export function registerAccount(input: MobileRegistrationInput): Promise<MobileRegistrationResponse> {
  return performRequest<MobileRegistrationResponse>(
    "/api/v1/auth/register/",
    { method: "POST", body: JSON.stringify(input) },
    false,
    false,
  );
}

export function resendVerificationEmail(email: string): Promise<{ detail: string }> {
  return performRequest<{ detail: string }>(
    "/api/v1/auth/resend-verification/",
    { method: "POST", body: JSON.stringify({ email }) },
    false,
    false,
  );
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

export function registerExpoPushToken(input: {
  token: string;
  platform: "ios" | "android";
  previous_token?: string;
}): Promise<{ registered: boolean }> {
  return performRequest<{ registered: boolean }>(
    "/api/v1/push-tokens/register/",
    { method: "POST", body: JSON.stringify(input) },
    true,
    true,
  );
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

export function markNotificationRead(notificationId: number): Promise<MobileNotification> {
  return performRequest<MobileNotification>(
    `/api/v1/notifications/${notificationId}/read/`,
    { method: "POST" },
    true,
    true,
  );
}

export function markAllNotificationsRead(): Promise<{ updated_count: number }> {
  return performRequest<{ updated_count: number }>(
    "/api/v1/notifications/read-all/",
    { method: "POST" },
    true,
    true,
  );
}

export function getManagerMechanicPage(page: number, pageSize = 20): Promise<ManagerMechanicPage> {
  return performRequest<ManagerMechanicPage>(
    `/api/v1/manager/mechanics/?page=${page}&page_size=${pageSize}`,
    {},
    true,
    true,
  );
}

export function getManagerQueuePage(page: number): Promise<ManagerQueuePage> {
  return performRequest<ManagerQueuePage>(`/api/v1/manager/queue/?page=${page}`, {}, true, true);
}

export function claimManagerRequest(requestId: number, mechanicId: number): Promise<ServiceRequest> {
  return performRequest<ServiceRequest>(
    `/api/v1/manager/queue/${requestId}/claim/`,
    { method: "POST", body: JSON.stringify({ mechanic_id: mechanicId }) },
    true,
    true,
  );
}

export function getRequest(requestId: number): Promise<ServiceRequest> {
  return performRequest<ServiceRequest>(`/api/v1/requests/${requestId}/`, {}, true, true);
}

export function createRequest(input: RequestCreateInput): Promise<ServiceRequest> {
  return performRequest<ServiceRequest>(
    "/api/v1/requests/",
    { method: "POST", body: JSON.stringify(input) },
    true,
    true,
  );
}

export function performMechanicRequestAction(
  requestId: number,
  action: MechanicRequestAction,
): Promise<ServiceRequest> {
  return performRequest<ServiceRequest>(
    `/api/v1/requests/${requestId}/actions/`,
    { method: "POST", body: JSON.stringify({ action }) },
    true,
    true,
  );
}

async function sendLogout(tokens: TokenPair, pushToken: string | null): Promise<Response> {
  return fetch(apiUrl("/api/v1/auth/logout/"), {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      Authorization: `Bearer ${tokens.access}`,
    },
    body: JSON.stringify({
      refresh: tokens.refresh,
      ...(pushToken ? { push_token: pushToken } : {}),
    }),
  });
}

export async function signOut(): Promise<void> {
  try {
    let tokens = await readStoredTokens();
    const pushToken = await readStoredPushToken();
    if (!tokens || !isApiConfigured()) return;

    let response: Response;
    try {
      response = await sendLogout(tokens, pushToken);
    } catch {
      return;
    }

    if (response.status === 401 && (await refreshSession())) {
      tokens = await readStoredTokens();
      if (tokens) {
        try {
          response = await sendLogout(tokens, pushToken);
        } catch {
          return;
        }
      }
    }

    if (response.ok) await deleteStoredPushToken();
  } finally {
    await clearStoredTokens();
  }
}
