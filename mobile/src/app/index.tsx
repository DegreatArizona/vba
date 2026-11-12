import { Redirect } from "expo-router";

import { LoadingScreen } from "@/components/LoadingScreen";
import { SessionRecovery } from "@/components/SessionRecovery";
import { useAuth } from "@/lib/auth";

export default function IndexRoute() {
  const { user, isLoading, hasStoredSession, sessionError } = useAuth();

  if (isLoading) return <LoadingScreen />;
  if (hasStoredSession && sessionError) return <SessionRecovery />;
  if (user) return <Redirect href="/(app)" />;
  return <Redirect href="/sign-in" />;
}
