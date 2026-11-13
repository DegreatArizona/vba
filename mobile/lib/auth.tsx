import { createContext, useCallback, useContext, useEffect, useMemo, useRef, type PropsWithChildren } from "react";
import useSWR, { useSWRConfig } from "swr";

import { getCurrentUser, signIn as signInRequest, signOut as signOutRequest } from "./api";
import { clearStoredTokens, readStoredTokens } from "./token-storage";
import { registerDevicePushToken } from "./push-notifications";
import type { MobileUser, TokenPair } from "./types";

interface AuthContextValue {
  user: MobileUser | null;
  isLoading: boolean;
  hasStoredSession: boolean;
  sessionError: Error | undefined;
  signIn: (username: string, password: string) => Promise<MobileUser>;
  signOut: () => Promise<void>;
  retrySession: () => Promise<MobileUser | null | undefined>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const { mutate: mutateCache } = useSWRConfig();
  const {
    data: tokens,
    isLoading: isReadingTokens,
    mutate: mutateTokens,
  } = useSWR<TokenPair | null>("auth:tokens", readStoredTokens, {
    revalidateOnFocus: false,
    revalidateOnReconnect: false,
    shouldRetryOnError: false,
  });
  const {
    data: user,
    error: sessionError,
    isLoading: isReadingUser,
    mutate: mutateUser,
  } = useSWR<MobileUser | null>(tokens ? "auth:user" : null, getCurrentUser, {
    revalidateOnFocus: false,
    revalidateOnReconnect: false,
    shouldRetryOnError: false,
  });

  const signIn = useCallback(
    async (username: string, password: string) => {
      const signedInUser = await signInRequest(username, password);
      await mutateTokens(await readStoredTokens(), { revalidate: false });
      await mutateCache("auth:user", signedInUser, { revalidate: false });
      return signedInUser;
    },
    [mutateCache, mutateTokens],
  );

  const signOut = useCallback(async () => {
    try {
      await signOutRequest();
    } finally {
      await clearStoredTokens();
      await mutateTokens(null, { revalidate: false });
      await mutateCache("auth:user", null, { revalidate: false });
    }
  }, [mutateCache, mutateTokens]);

  const retrySession = useCallback(() => mutateUser(), [mutateUser]);
  const pushRegistrationForUser = useRef<number | null>(null);

  useEffect(() => {
    if (!user) {
      pushRegistrationForUser.current = null;
      return;
    }
    if (pushRegistrationForUser.current === user.id) return;

    pushRegistrationForUser.current = user.id;
    void registerDevicePushToken().catch(() => {
      pushRegistrationForUser.current = null;
    });
  }, [user]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: user ?? null,
      isLoading: isReadingTokens || Boolean(tokens && isReadingUser),
      hasStoredSession: Boolean(tokens),
      sessionError,
      signIn,
      signOut,
      retrySession,
    }),
    [
      user,
      isReadingTokens,
      tokens,
      isReadingUser,
      sessionError,
      signIn,
      signOut,
      retrySession,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider.");
  return context;
}
