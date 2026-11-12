import type { PropsWithChildren } from "react";
import { ScrollView, StyleSheet, View, type ViewStyle } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { colors } from "../lib/theme";

interface ScreenFrameProps extends PropsWithChildren {
  contentStyle?: ViewStyle;
  scroll?: boolean;
}

export function ScreenFrame({ children, contentStyle, scroll = true }: ScreenFrameProps) {
  return (
    <SafeAreaView edges={["top", "left", "right"]} style={styles.safeArea}>
      {scroll ? (
        <ScrollView
          contentContainerStyle={[styles.content, contentStyle]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {children}
        </ScrollView>
      ) : (
        <View style={[styles.content, contentStyle]}>{children}</View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.canvas,
  },
  content: {
    width: "100%",
    maxWidth: 680,
    alignSelf: "center",
    flexGrow: 1,
    paddingHorizontal: 22,
    paddingVertical: 24,
  },
});
