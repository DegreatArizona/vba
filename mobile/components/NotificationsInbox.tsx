import { useMemo } from "react";
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from "react-native";
import useSWRInfinite from "swr/infinite";

import { NotificationCard } from "./NotificationCard";
import { PrimaryButton } from "./PrimaryButton";
import { useAuth } from "../lib/auth";
import { ApiError, getApiConfigurationIssue, getNotificationPage, isApiConfigured } from "../lib/api";
import { colors } from "../lib/theme";
import type { NotificationPage } from "../lib/types";

export function NotificationsInbox() {
  const { user } = useAuth();
  const getKey = (pageIndex: number, previousPage: NotificationPage | null) => {
    if (!isApiConfigured() || !user) return null;
    if (pageIndex > 0 && !previousPage?.next) return null;
    return pageIndex === 0 ? "/api/v1/notifications/" : previousPage?.next ?? null;
  };

  const { data, error, isLoading, isValidating, size, setSize, mutate } =
    useSWRInfinite<NotificationPage>(getKey, getNotificationPage, {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      shouldRetryOnError: false,
    });
  const notifications = useMemo(() => data?.flatMap((page) => page.results) ?? [], [data]);
  const unreadCount = notifications.filter((notification) => !notification.is_read).length;
  const lastPage = data?.[data.length - 1];
  const configurationIssue = getApiConfigurationIssue();

  if (!user) return null;

  return (
    <ScrollView
      contentContainerStyle={styles.scrollContent}
      refreshControl={
        <RefreshControl
          colors={[colors.teal]}
          onRefresh={() => void mutate()}
          refreshing={Boolean(isValidating && data)}
          tintColor={colors.teal}
        />
      }
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.container}>
        <View style={styles.header}>
          <View style={styles.headerCopy}>
            <Text style={styles.eyebrow}>ACCOUNT ACTIVITY</Text>
            <Text style={styles.title}>Notifications</Text>
            <Text style={styles.subtitle}>Updates sent to your Auto Aid account, newest first.</Text>
          </View>
          <View style={styles.unreadSummary}>
            <Text style={styles.unreadCount}>{String(unreadCount)}</Text>
            <Text style={styles.unreadLabel}>NEW</Text>
          </View>
        </View>

        <Text style={styles.readOnlyNote}>
          The count covers loaded notifications. Viewing the inbox does not mark them as read.
        </Text>

        {configurationIssue ? (
          <StateCard title="Connect the service API" body={configurationIssue} />
        ) : error ? (
          <StateCard
            title={error instanceof ApiError && error.status === 401 ? "Session expired" : "Could not load notifications"}
            body={error.message ?? "Check your connection and try again."}
          />
        ) : isLoading ? (
          <View style={styles.loadingCard}>
            <ActivityIndicator color={colors.teal} />
            <Text style={styles.loadingText}>Loading notifications</Text>
          </View>
        ) : notifications.length ? (
          <View style={styles.notificationList}>
            {notifications.map((notification) => (
              <NotificationCard key={notification.id} notification={notification} />
            ))}
            {lastPage?.next ? (
              <PrimaryButton
                disabled={isValidating}
                label="Load more"
                loading={isValidating && size > (data?.length ?? 0)}
                onPress={() => void setSize(size + 1)}
                style={styles.loadMore}
              />
            ) : null}
          </View>
        ) : (
          <StateCard title="No notifications yet" body="New account updates will appear here." />
        )}

        {error && !(error instanceof ApiError && error.status === 401) ? (
          <Pressable accessibilityRole="button" onPress={() => void mutate()} style={styles.retry}>
            <Text style={styles.retryText}>Try again</Text>
          </Pressable>
        ) : null}

        {isValidating && data ? <ActivityIndicator color={colors.teal} style={styles.refreshIndicator} /> : null}
      </View>
    </ScrollView>
  );
}

function StateCard({ title, body }: { title: string; body: string }) {
  return (
    <View style={styles.stateCard}>
      <View style={styles.stateMark} />
      <View style={styles.stateCopy}>
        <Text style={styles.stateTitle}>{title}</Text>
        <Text style={styles.stateBody}>{body}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 32,
    backgroundColor: colors.canvas,
  },
  container: {
    width: "100%",
    maxWidth: 680,
    alignSelf: "center",
    gap: 18,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 18,
  },
  headerCopy: {
    flex: 1,
    gap: 5,
  },
  eyebrow: {
    color: colors.teal,
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 1.1,
  },
  title: {
    color: colors.ink,
    fontSize: 30,
    lineHeight: 36,
    fontWeight: "700",
  },
  subtitle: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 19,
  },
  unreadSummary: {
    minWidth: 70,
    minHeight: 70,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 18,
    backgroundColor: colors.ink,
  },
  unreadCount: {
    color: colors.white,
    fontSize: 25,
    lineHeight: 29,
    fontWeight: "700",
  },
  unreadLabel: {
    marginTop: 2,
    color: "#D4DEDE",
    fontSize: 9,
    fontWeight: "700",
    letterSpacing: 1,
  },
  readOnlyNote: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
  },
  notificationList: {
    gap: 10,
  },
  loadingCard: {
    minHeight: 120,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    borderRadius: 20,
    backgroundColor: colors.paper,
    borderWidth: 1,
    borderColor: colors.line,
  },
  loadingText: {
    color: colors.muted,
    fontSize: 14,
  },
  stateCard: {
    flexDirection: "row",
    gap: 13,
    padding: 20,
    borderRadius: 20,
    backgroundColor: colors.paper,
    borderWidth: 1,
    borderColor: colors.line,
  },
  stateMark: {
    width: 9,
    height: 9,
    marginTop: 6,
    borderRadius: 5,
    backgroundColor: colors.amber,
  },
  stateCopy: {
    flex: 1,
    gap: 5,
  },
  stateTitle: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: "700",
  },
  stateBody: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 19,
  },
  loadMore: {
    marginTop: 3,
  },
  retry: {
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  retryText: {
    color: colors.teal,
    fontSize: 14,
    fontWeight: "700",
  },
  refreshIndicator: {
    marginTop: 4,
  },
});
