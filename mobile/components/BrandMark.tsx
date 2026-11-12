import { Image, StyleSheet } from "react-native";

interface BrandMarkProps {
  size?: number;
}

export function BrandMark({ size = 52 }: BrandMarkProps) {
  return (
    <Image
      accessibilityLabel="Auto Aid vehicle assistance mark"
      accessible
      resizeMode="cover"
      source={require("../assets/images/icon.png")}
      style={[styles.mark, { width: size, height: size, borderRadius: size * 0.26 }]}
    />
  );
}

const styles = StyleSheet.create({
  mark: {
    backgroundColor: "#18303C",
  },
});
