import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { colors } from "../lib/theme";

interface LoadingScreenProps {
  label?: string;
}

export function LoadingScreen({ label = "Loading your account" }: LoadingScreenProps) {
  return (
    <SafeAreaView style={styles.safeArea}>
      <View accessibilityRole="progressbar" style={styles.container}>
        <ActivityIndicator color={colors.teal} size="large" />
        <Text style={styles.label}>{label}</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.canvas,
  },
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 14,
  },
  label: {
    color: colors.muted,
    fontSize: 15,
  },
});
