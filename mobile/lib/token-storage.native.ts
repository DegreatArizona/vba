import * as SecureStore from "expo-secure-store";
import type { TokenPair } from "./types";

const ACCESS_TOKEN_KEY = "autoaid.access-token";
const REFRESH_TOKEN_KEY = "autoaid.refresh-token";
const secureOptions = {
  keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
};

export async function readStoredTokens(): Promise<TokenPair | null> {
  const [access, refresh] = await Promise.all([
    SecureStore.getItemAsync(ACCESS_TOKEN_KEY, secureOptions),
    SecureStore.getItemAsync(REFRESH_TOKEN_KEY, secureOptions),
  ]);

  if (!access || !refresh) {
    await clearStoredTokens();
    return null;
  }

  return { access, refresh };
}

export async function writeStoredTokens(tokens: TokenPair): Promise<void> {
  try {
    await Promise.all([
      SecureStore.setItemAsync(ACCESS_TOKEN_KEY, tokens.access, secureOptions),
      SecureStore.setItemAsync(REFRESH_TOKEN_KEY, tokens.refresh, secureOptions),
    ]);
  } catch (error) {
    await clearStoredTokens();
    throw error;
  }
}

export async function clearStoredTokens(): Promise<void> {
  await Promise.all([
    SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY, secureOptions),
    SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY, secureOptions),
  ]);
}
