import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors } from "../lib/theme";
import type { ServiceRequest } from "../lib/types";

interface RequestCardProps {
  onPress: () => void;
  request: ServiceRequest;
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function statusPalette(status: string) {
  const value = status.toLowerCase();
  if (value.includes("complete") || value.includes("closed")) {
    return { background: colors.tealSoft, foreground: colors.teal };
  }
  if (value.includes("cancel")) {
    return { background: colors.redSoft, foreground: colors.red };
  }
  return { background: colors.amberSoft, foreground: "#805311" };
}

export function RequestCard({ onPress, request }: RequestCardProps) {
  const status = request.status?.replace(/[_-]/g, " ").trim() || "Status unavailable";
  const palette = statusPalette(status);
  const vehicle = [request.vehicle_name, request.vehicle_no].filter(Boolean).join(" · ");
  const place = [request.location, request.state].filter(Boolean).join(", ");

  return (
    <Pressable
      accessibilityHint="Opens details for this service request."
      accessibilityLabel={`Request ${request.id}: ${request.category}, status ${status}. View details.`}
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
    >
      <View style={styles.topLine}>
        <Text style={styles.category}>{request.category || "Vehicle assistance"}</Text>
        <View style={[styles.status, { backgroundColor: palette.background }]}>
          <Text accessibilityLabel={`Request status: ${status}`} style={[styles.statusText, { color: palette.foreground }]}>
            {status}
          </Text>
        </View>
      </View>
      <Text style={styles.requestId}>Request #{request.id}</Text>
      {vehicle ? <Text style={styles.vehicle}>{vehicle}</Text> : null}
      {place ? <Text numberOfLines={2} style={styles.location}>{place}</Text> : null}
      {request.problem_description ? (
        <Text numberOfLines={3} style={styles.description}>{request.problem_description}</Text>
      ) : null}
      <View style={styles.footer}>
        <Text style={styles.footerLabel}>Submitted</Text>
        <Text style={styles.footerValue}>{formatDate(request.date)}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 17,
    gap: 7,
    borderRadius: 19,
    backgroundColor: colors.paper,
    borderWidth: 1,
    borderColor: colors.line,
  },
  cardPressed: {
    borderColor: colors.teal,
    opacity: 0.9,
  },
  topLine: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
  },
  category: {
    flex: 1,
    color: colors.ink,
    fontSize: 16,
    fontWeight: "700",
  },
  status: {
    maxWidth: "55%",
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  statusText: {
    fontSize: 11,
    fontWeight: "700",
    textTransform: "capitalize",
  },
  requestId: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "600",
  },
  vehicle: {
    marginTop: 3,
    color: colors.inkSoft,
    fontSize: 14,
    fontWeight: "600",
  },
  location: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 19,
  },
  description: {
    marginTop: 4,
    color: colors.inkSoft,
    fontSize: 13,
    lineHeight: 19,
  },
  footer: {
    marginTop: 9,
    paddingTop: 11,
    borderTopWidth: 1,
    borderTopColor: colors.line,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  footerLabel: {
    color: colors.muted,
    fontSize: 12,
  },
  footerValue: {
    color: colors.inkSoft,
    fontSize: 12,
    fontWeight: "600",
  },
});
