import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors } from "../lib/theme";
import type { MobileNotification } from "../lib/types";

export function NotificationCard({
  notification,
  isUpdating = false,
  onMarkRead,
}: {
  notification: MobileNotification;
  isUpdating?: boolean;
  onMarkRead?: () => void;
}) {
  const status = notification.is_read ? "Read" : "New";
  const timestamp = formatTimestamp(notification.timestamp);
  const cardContent = (
    <>
      <View style={styles.statusColumn}>
        <View style={[styles.statusDot, !notification.is_read && styles.statusDotUnread]} />
        <Text style={[styles.statusLabel, !notification.is_read && styles.statusLabelUnread]}>
          {isUpdating ? "Saving" : status}
        </Text>
      </View>
      <View style={styles.copy}>
        <Text style={styles.message}>{notification.message}</Text>
        <Text style={styles.timestamp}>{timestamp}</Text>
        {!notification.is_read ? <Text style={styles.actionHint}>Tap to mark as read</Text> : null}
      </View>
    </>
  );
  const accessibilityLabel = notification.is_read
    ? `Read notification. ${notification.message}. ${timestamp}.`
    : `Mark notification as read. ${notification.message}. ${timestamp}.`;

  if (notification.is_read) {
    return (
      <View accessible accessibilityLabel={accessibilityLabel} style={styles.card}>
        {cardContent}
      </View>
    );
  }

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityState={{ disabled: isUpdating }}
      disabled={isUpdating}
      onPress={onMarkRead}
      style={({ pressed }) => [styles.card, styles.unreadCard, pressed && styles.pressedCard]}
    >
      {cardContent}
    </Pressable>
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
  pressedCard: {
    opacity: 0.82,
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
  actionHint: {
    color: colors.teal,
    fontSize: 11,
    fontWeight: "700",
  },
});
