import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { SWRConfig } from "swr";

import { AuthProvider } from "@/lib/auth";
import { colors } from "@/lib/theme";

export default function RootLayout() {
  return (
    <SWRConfig value={{ revalidateOnFocus: false, revalidateOnReconnect: false, shouldRetryOnError: false }}>
      <SafeAreaProvider>
        <AuthProvider>
          <StatusBar style="dark" />
          <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.canvas } }} />
        </AuthProvider>
      </SafeAreaProvider>
    </SWRConfig>
  );
}
