import { useMemo } from "react";
import { useRouter } from "expo-router";
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from "react-native";
import useSWRInfinite from "swr/infinite";

import { BrandMark } from "./BrandMark";
import { PrimaryButton } from "./PrimaryButton";
import { RequestCard } from "./RequestCard";
import { ScreenFrame } from "./ScreenFrame";
import { useAuth } from "../lib/auth";
import { ApiError, getApiConfigurationIssue, getRequestPage, isApiConfigured } from "../lib/api";
import { colors } from "../lib/theme";
import type { RequestPage, UserRole } from "../lib/types";

const roleCopy: Record<UserRole, { title: string; description: string }> = {
  driver: {
    title: "Your assistance",
    description: "A clear view of the vehicle service requests linked to your account.",
  },
  mechanic: {
    title: "Assigned jobs",
    description: "The service requests currently assigned to your mechanic profile.",
  },
  manager: {
    title: "Team requests",
    description: "Requests assigned to your manager profile, all in one place.",
  },
};

export function RequestDashboard() {
  const router = useRouter();
  const { user } = useAuth();
  const canReadRequests = Boolean(
    user?.is_email_verified && (user.role === "driver" || user.is_approved),
  );

  const getKey = (pageIndex: number, previousPage: RequestPage | null) => {
    if (!isApiConfigured() || !canReadRequests) return null;
    if (pageIndex > 0 && !previousPage?.next) return null;
    return pageIndex === 0 ? "/api/v1/requests/" : previousPage?.next ?? null;
  };

  const { data, error, isLoading, isValidating, size, setSize, mutate } = useSWRInfinite<RequestPage>(
    getKey,
    getRequestPage,
    { revalidateOnFocus: false, revalidateOnReconnect: false, shouldRetryOnError: false },
  );

  const requests = useMemo(() => data?.flatMap((page) => page.results) ?? [], [data]);
  const activeCount = requests.filter((request) => {
    const status = request.status.toLowerCase();
    return !["complete", "closed", "cancel", "released"].some((finishedStatus) =>
      status.includes(finishedStatus),
    );
  }).length;
  const lastPage = data?.[data.length - 1];
  const copy = user ? roleCopy[user.role] : roleCopy.driver;

  if (!user) return null;

  if (!user.is_email_verified) {
    return (
      <ScreenFrame contentStyle={styles.centerContent}>
        <StateCard
          title="Verify your email first"
          body="Your account can sign in, but the service request list is available after your email is verified."
        />
      </ScreenFrame>
    );
  }

  if (user.role !== "driver" && !user.is_approved) {
    return (
      <ScreenFrame contentStyle={styles.centerContent}>
        <StateCard
          title="Your profile is awaiting approval"
          body="Request access will appear here after Auto Aid approves your profile."
        />
      </ScreenFrame>
    );
  }

  const configurationIssue = getApiConfigurationIssue();

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
        <View style={styles.topBar}>
          <View style={styles.brand}>
            <BrandMark size={42} />
            <View>
              <Text style={styles.brandName}>Auto Aid</Text>
              <Text style={styles.brandCaption}>ROADSIDE SUPPORT</Text>
            </View>
          </View>
          <View style={styles.roleBadge}>
            <Text style={styles.roleBadgeText}>{user.role}</Text>
          </View>
        </View>

        <View style={styles.heading}>
          <Text style={styles.eyebrow}>GOOD TO SEE YOU, {user.first_name || user.username}</Text>
          <Text style={styles.title}>{copy.title}</Text>
          <Text style={styles.description}>{copy.description}</Text>
        </View>

        {user.role === "driver" ? (
          <View style={styles.requestAction}>
            <PrimaryButton
              label="Request roadside assistance"
              onPress={() => router.push("/(app)/request-assistance")}
            />
            <Text style={styles.requestActionNote}>
              Describe the problem and location. Pricing and payment are handled after review.
            </Text>
          </View>
        ) : null}

        <View style={styles.metricsRow}>
          <MetricCard label="REQUESTS" value={String(requests.length)} />
          <MetricCard label="ACTIVE" value={String(activeCount)} accent />
        </View>

        {configurationIssue ? (
          <StateCard title="Connect the service API" body={configurationIssue} compact />
        ) : null}

        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>Recent requests</Text>
            <Text style={styles.sectionCaption}>Read-only activity from your Auto Aid account</Text>
          </View>
          {isValidating && data ? <ActivityIndicator color={colors.teal} /> : null}
        </View>

        {error ? (
          <StateCard
            title={error instanceof ApiError && error.status === 401 ? "Session expired" : "Could not load requests"}
            body={error.message ?? "Check your connection and try again."}
            compact
          />
        ) : isLoading ? (
          <View style={styles.loadingCard}>
            <ActivityIndicator color={colors.teal} />
            <Text style={styles.loadingText}>Loading your requests</Text>
          </View>
        ) : requests.length ? (
          <View style={styles.requestList}>
            {requests.map((request) => (
              <RequestCard
                key={request.id}
                onPress={() => router.push({ pathname: "/(app)/request-details", params: { requestId: String(request.id) } })}
                request={request}
              />
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
          <StateCard
            title="No requests to show yet"
            body="Start a roadside service request and track its review here."
            compact
          />
        )}

        {error && !(error instanceof ApiError && error.status === 401) ? (
          <Pressable accessibilityRole="button" onPress={() => void mutate()} style={styles.retry}>
            <Text style={styles.retryText}>Try again</Text>
          </Pressable>
        ) : null}
      </View>
    </ScrollView>
  );
}

function MetricCard({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return (
    <View style={[styles.metricCard, accent && styles.metricAccent]}>
      <Text style={[styles.metricLabel, accent && styles.metricAccentLabel]}>{label}</Text>
      <Text style={[styles.metricValue, accent && styles.metricAccentText]}>{value}</Text>
    </View>
  );
}

function StateCard({ title, body, compact = false }: { title: string; body: string; compact?: boolean }) {
  return (
    <View style={[styles.stateCard, compact && styles.stateCardCompact]}>
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
    paddingTop: 15,
    paddingBottom: 28,
    backgroundColor: colors.canvas,
  },
  container: {
    width: "100%",
    maxWidth: 680,
    alignSelf: "center",
    gap: 20,
  },
  topBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  brand: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  brandName: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "700",
  },
  brandCaption: {
    marginTop: 2,
    color: colors.muted,
    fontSize: 9,
    fontWeight: "700",
    letterSpacing: 1.1,
  },
  roleBadge: {
    borderRadius: 999,
    paddingHorizontal: 13,
    paddingVertical: 8,
    backgroundColor: colors.tealSoft,
  },
  roleBadgeText: {
    color: colors.teal,
    fontSize: 12,
    fontWeight: "700",
    textTransform: "capitalize",
  },
  heading: {
    gap: 7,
    marginTop: 6,
  },
  eyebrow: {
    color: colors.teal,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1.05,
    textTransform: "uppercase",
  },
  title: {
    color: colors.ink,
    fontSize: 30,
    lineHeight: 36,
    fontWeight: "700",
  },
  description: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 21,
  },
  requestAction: {
    gap: 8,
  },
  requestActionNote: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
  },
  metricsRow: {
    flexDirection: "row",
    gap: 12,
  },
  metricCard: {
    flex: 1,
    minHeight: 96,
    justifyContent: "space-between",
    borderRadius: 18,
    padding: 16,
    backgroundColor: colors.paper,
    borderWidth: 1,
    borderColor: colors.line,
  },
  metricAccent: {
    backgroundColor: colors.ink,
    borderColor: colors.ink,
  },
  metricLabel: {
    color: colors.muted,
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 1,
  },
  metricValue: {
    color: colors.ink,
    fontSize: 27,
    fontWeight: "700",
  },
  metricAccentLabel: {
    color: "#D4DEDE",
  },
  metricAccentText: {
    color: colors.white,
  },
  sectionHeader: {
    marginTop: 3,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
  },
  sectionTitle: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "700",
  },
  sectionCaption: {
    marginTop: 4,
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
  },
  requestList: {
    gap: 12,
  },
  loadMore: {
    marginTop: 3,
  },
  loadingCard: {
    minHeight: 110,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    borderRadius: 18,
    backgroundColor: colors.paper,
    borderWidth: 1,
    borderColor: colors.line,
  },
  loadingText: {
    color: colors.muted,
    fontSize: 14,
  },
  stateCard: {
    width: "100%",
    maxWidth: 520,
    alignSelf: "center",
    flexDirection: "row",
    gap: 13,
    padding: 20,
    borderRadius: 20,
    backgroundColor: colors.paper,
    borderWidth: 1,
    borderColor: colors.line,
  },
  stateCardCompact: {
    maxWidth: undefined,
    alignSelf: "stretch",
    padding: 16,
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
  centerContent: {
    justifyContent: "center",
  },
  retry: {
    alignSelf: "center",
    minHeight: 44,
    justifyContent: "center",
    paddingHorizontal: 18,
  },
  retryText: {
    color: colors.teal,
    fontSize: 14,
    fontWeight: "700",
  },
});
