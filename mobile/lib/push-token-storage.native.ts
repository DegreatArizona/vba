import * as SecureStore from "expo-secure-store";

const PUSH_TOKEN_KEY = "autoaid.expo-push-token";
const secureOptions = {
  keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
};

export function readStoredPushToken(): Promise<string | null> {
  return SecureStore.getItemAsync(PUSH_TOKEN_KEY, secureOptions);
}

export function writeStoredPushToken(token: string): Promise<void> {
  return SecureStore.setItemAsync(PUSH_TOKEN_KEY, token, secureOptions);
}

export function deleteStoredPushToken(): Promise<void> {
  return SecureStore.deleteItemAsync(PUSH_TOKEN_KEY, secureOptions);
}
