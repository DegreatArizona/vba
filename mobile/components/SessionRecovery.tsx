import { StyleSheet, Text, View } from "react-native";

import { useAuth } from "../lib/auth";
import { colors } from "../lib/theme";
import { PrimaryButton } from "./PrimaryButton";
import { ScreenFrame } from "./ScreenFrame";

export function SessionRecovery() {
  const { sessionError, retrySession, signOut } = useAuth();

  return (
    <ScreenFrame contentStyle={styles.content}>
      <View style={styles.card}>
        <Text style={styles.eyebrow}>ACCOUNT CONNECTION</Text>
        <Text style={styles.title}>We could not restore your session.</Text>
        <Text accessibilityLiveRegion="polite" style={styles.body}>
          {sessionError?.message ?? "Check your connection, then try again."}
        </Text>
        <PrimaryButton label="Try again" onPress={() => void retrySession()} style={styles.button} />
        <Text
          accessibilityRole="button"
          onPress={() => void signOut()}
          style={styles.signOut}
        >
          Sign out and return to sign in
        </Text>
      </View>
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  content: {
    justifyContent: "center",
  },
  card: {
    borderRadius: 24,
    backgroundColor: colors.paper,
    padding: 24,
    gap: 14,
    borderWidth: 1,
    borderColor: colors.line,
  },
  eyebrow: {
    color: colors.teal,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1.2,
  },
  title: {
    color: colors.ink,
    fontSize: 25,
    lineHeight: 31,
    fontWeight: "700",
  },
  body: {
    color: colors.muted,
    fontSize: 15,
    lineHeight: 22,
  },
  button: {
    marginTop: 8,
  },
  signOut: {
    alignSelf: "center",
    padding: 10,
    color: colors.inkSoft,
    fontSize: 14,
    fontWeight: "600",
  },
});
