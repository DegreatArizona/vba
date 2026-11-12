import { StyleSheet, Text, View } from "react-native";

import { colors } from "../lib/theme";
import type { MobileNotification } from "../lib/types";

export function NotificationCard({ notification }: { notification: MobileNotification }) {
  const status = notification.is_read ? "Read" : "New";
  const timestamp = formatTimestamp(notification.timestamp);

  return (
    <View
      accessible
      accessibilityLabel={`${status} notification. ${notification.message}. ${timestamp}.`}
      style={[styles.card, !notification.is_read && styles.unreadCard]}
    >
      <View style={styles.statusColumn}>
        <View style={[styles.statusDot, !notification.is_read && styles.statusDotUnread]} />
        <Text style={[styles.statusLabel, !notification.is_read && styles.statusLabelUnread]}>{status}</Text>
      </View>
      <View style={styles.copy}>
        <Text style={styles.message}>{notification.message}</Text>
        <Text style={styles.timestamp}>{timestamp}</Text>
      </View>
    </View>
  );
}

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Date unavailable";
  return date.toLocaleString(undefined, {
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    month: "short",
    year: "numeric",
  });
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 14,
    padding: 18,
    borderRadius: 18,
    backgroundColor: colors.paper,
    borderWidth: 1,
    borderColor: colors.line,
  },
  unreadCard: {
    backgroundColor: colors.tealSoft,
    borderColor: "#C8E7DF",
  },
  statusColumn: {
    minWidth: 40,
    alignItems: "center",
    gap: 6,
  },
  statusDot: {
    width: 8,
    height: 8,
    marginTop: 4,
    borderRadius: 5,
    backgroundColor: colors.muted,
  },
  statusDotUnread: {
    backgroundColor: colors.teal,
  },
  statusLabel: {
    color: colors.muted,
    fontSize: 10,
    fontWeight: "700",
  },
  statusLabelUnread: {
    color: colors.teal,
  },
  copy: {
    flex: 1,
    gap: 8,
  },
  message: {
    color: colors.ink,
    fontSize: 14,
    lineHeight: 21,
  },
  timestamp: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: "600",
  },
});
