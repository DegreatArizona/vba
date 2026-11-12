import { Redirect } from "expo-router";

import { LoadingScreen } from "@/components/LoadingScreen";
import { SignInScreen } from "@/components/SignInScreen";
import { SessionRecovery } from "@/components/SessionRecovery";
import { useAuth } from "@/lib/auth";

export default function SignInRoute() {
  const { user, isLoading, hasStoredSession, sessionError } = useAuth();

  if (isLoading) return <LoadingScreen />;
  if (user) return <Redirect href="/(app)" />;
  if (hasStoredSession && sessionError) return <SessionRecovery />;
  return <SignInScreen />;
}
