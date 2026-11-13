import Constants from "expo-constants";
import * as Notifications from "expo-notifications";
import { AndroidImportance } from "expo-notifications";
import { Platform } from "react-native";

import { registerExpoPushToken } from "./api";
import { readStoredPushToken, writeStoredPushToken } from "./push-token-storage";

export async function registerDevicePushToken(): Promise<void> {
  const platform = Platform.OS;
  if (platform !== "ios" && platform !== "android") return;

  const projectId = Constants.expoConfig?.extra?.eas?.projectId ?? Constants.easConfig?.projectId;
  if (!projectId) return;

  if (platform === "android") {
    await Notifications.setNotificationChannelAsync("default", {
      name: "Default",
      importance: AndroidImportance.MAX,
    });
  }

  const permission = await Notifications.getPermissionsAsync();
  const granted =
    permission.status === "granted" ? permission : await Notifications.requestPermissionsAsync();
  if (granted.status !== "granted") return;

  const token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;
  const previousToken = await readStoredPushToken();

  await registerExpoPushToken({
    token,
    platform,
    ...(previousToken && previousToken !== token ? { previous_token: previousToken } : {}),
  });
  await writeStoredPushToken(token);
}
