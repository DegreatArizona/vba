import { useMemo } from "react";
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, Text, View } from "react-native";
import useSWRInfinite from "swr/infinite";

import { BrandMark } from "./BrandMark";
import { PrimaryButton } from "./PrimaryButton";
import { ScreenFrame } from "./ScreenFrame";
import { useAuth } from "../lib/auth";
import {
  ApiError,
  getApiConfigurationIssue,
  getManagerMechanicPage,
  isApiConfigured,
} from "../lib/api";
import { colors } from "../lib/theme";
import type { ManagerMechanicPage, ManagerMechanicSummary } from "../lib/types";

export function ManagerTeamScreen() {
  const { user } = useAuth();
  const canReadTeam = Boolean(
    user?.role === "manager" && user.is_email_verified && user.is_approved && isApiConfigured(),
  );

  const getKey = (pageIndex: number, previousPage: ManagerMechanicPage | null) => {
    if (!canReadTeam) return null;
    if (pageIndex > 0 && !previousPage?.next) return null;
    return String(pageIndex + 1);
  };

  const { data, error, isLoading, isValidating, size, setSize, mutate } =
    useSWRInfinite<ManagerMechanicPage>(
      getKey,
      (pageNumber) => getManagerMechanicPage(Number(pageNumber)),
      {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      shouldRetryOnError: false,
    });

  const mechanics = useMemo(() => data?.flatMap((page) => page.results) ?? [], [data]);
  const lastPage = data?.[data.length - 1];
  const configurationIssue = getApiConfigurationIssue();

  if (!user) return null;

  if (user.role !== "manager") {
    return (
      <ScreenFrame contentStyle={styles.centerContent}>
        <NoticeCard title="Managers only" body="This workspace is available to manager accounts." />
      </ScreenFrame>
    );
  }

  if (!user.is_email_verified) {
    return (
      <ScreenFrame contentStyle={styles.centerContent}>
        <NoticeCard title="Verify your email first" body="Team access is available after your email is verified." />
      </ScreenFrame>
    );
  }

  if (!user.is_approved) {
    return (
      <ScreenFrame contentStyle={styles.centerContent}>
        <NoticeCard title="Manager approval pending" body="Your team view will appear after Auto Aid approves your profile." />
      </ScreenFrame>
    );
  }

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
              <Text style={styles.brandCaption}>MANAGER WORKSPACE</Text>
            </View>
          </View>
          <View style={styles.roleBadge}>
            <Text style={styles.roleBadgeText}>Manager</Text>
          </View>
        </View>

        <View style={styles.heading}>
          <Text style={styles.eyebrow}>PEOPLE & OPERATIONS</Text>
          <Text style={styles.title}>Your mechanic team</Text>
          <Text style={styles.description}>
            Mechanics linked to your manager profile, with request activity scoped to your account.
          </Text>
        </View>

        <View style={styles.privacyNote}>
          <Text style={styles.privacyTitle}>Team overview</Text>
          <Text style={styles.privacyText}>
            Contact, banking, and license details stay private. Use Activity to review your assigned requests.
          </Text>
        </View>

        {configurationIssue ? (
          <NoticeCard title="Connect the service API" body={configurationIssue} compact />
        ) : error ? (
          <NoticeCard
            title={error instanceof ApiError && error.status === 401 ? "Session expired" : "Could not load your team"}
            body={error.message ?? "Check your connection and try again."}
            compact
          />
        ) : isLoading ? (
          <View style={styles.loadingCard}>
            <ActivityIndicator color={colors.teal} />
            <Text style={styles.loadingText}>Loading your mechanics</Text>
          </View>
        ) : mechanics.length ? (
          <View style={styles.memberList}>
            <View style={styles.sectionHeader}>
              <View>
                <Text style={styles.sectionTitle}>Assigned mechanics</Text>
                <Text style={styles.sectionCaption}>{data?.[0]?.count ?? mechanics.length} team members</Text>
              </View>
              {isValidating ? <ActivityIndicator color={colors.teal} /> : null}
            </View>
            {mechanics.map((mechanic) => (
              <MechanicCard key={mechanic.id} mechanic={mechanic} />
            ))}
            {lastPage?.next ? (
              <PrimaryButton
                disabled={isValidating}
                label="Load more mechanics"
                loading={isValidating && size > (data?.length ?? 0)}
                onPress={() => void setSize(size + 1)}
              />
            ) : null}
          </View>
        ) : (
          <NoticeCard
            title="No mechanics linked yet"
            body="Mechanics assigned to your manager profile will appear here."
            compact
          />
        )}
      </View>
    </ScrollView>
  );
}

function MechanicCard({ mechanic }: { mechanic: ManagerMechanicSummary }) {
  const initials = mechanic.full_name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
  const serviceArea = [mechanic.local_government, mechanic.state].filter(Boolean).join(", ");

  return (
    <View style={styles.memberCard}>
      <View style={styles.memberHeader}>
        <View style={styles.identity}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{initials || "M"}</Text>
          </View>
          <View style={styles.memberCopy}>
            <Text style={styles.memberName}>{mechanic.full_name}</Text>
            <Text style={styles.memberUnion}>{mechanic.union_name || "Service partner"}</Text>
          </View>
        </View>
        <View style={[styles.approvalBadge, mechanic.is_approved && styles.approvalBadgeActive]}>
          <Text style={[styles.approvalText, mechanic.is_approved && styles.approvalTextActive]}>
            {mechanic.is_approved ? "Approved" : "Pending"}
          </Text>
        </View>
      </View>

      <Text style={styles.serviceArea}>{serviceArea || "Service area not listed"}</Text>

      <View style={styles.statsRow}>
        <View style={styles.statCell}>
          <Text style={styles.statLabel}>ASSIGNED</Text>
          <Text style={styles.statValue}>{mechanic.assigned_request_count}</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statCell}>
          <Text style={styles.statLabel}>ACTIVE</Text>
          <Text style={styles.statValue}>{mechanic.active_request_count}</Text>
        </View>
      </View>
    </View>
  );
}

function NoticeCard({ title, body, compact = false }: { title: string; body: string; compact?: boolean }) {
  return (
    <View style={[styles.noticeCard, compact && styles.noticeCardCompact]}>
      <View style={styles.noticeMark} />
      <View style={styles.noticeCopy}>
        <Text style={styles.noticeTitle}>{title}</Text>
        <Text style={styles.noticeBody}>{body}</Text>
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
  privacyNote: {
    gap: 5,
    borderRadius: 16,
    padding: 16,
    backgroundColor: colors.tealSoft,
  },
  privacyTitle: {
    color: colors.ink,
    fontSize: 14,
    fontWeight: "700",
  },
  privacyText: {
    color: colors.inkSoft,
    fontSize: 12,
    lineHeight: 18,
  },
  memberList: {
    gap: 12,
  },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    marginBottom: 2,
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
  },
  memberCard: {
    gap: 14,
    padding: 16,
    borderRadius: 18,
    backgroundColor: colors.paper,
    borderWidth: 1,
    borderColor: colors.line,
  },
  memberHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
  },
  identity: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    gap: 11,
  },
  avatar: {
    width: 42,
    height: 42,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 21,
    backgroundColor: colors.ink,
  },
  avatarText: {
    color: colors.white,
    fontSize: 13,
    fontWeight: "700",
  },
  memberCopy: {
    flex: 1,
    gap: 3,
  },
  memberName: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: "700",
  },
  memberUnion: {
    color: colors.muted,
    fontSize: 12,
  },
  approvalBadge: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
    backgroundColor: colors.amberSoft,
  },
  approvalBadgeActive: {
    backgroundColor: colors.tealSoft,
  },
  approvalText: {
    color: colors.inkSoft,
    fontSize: 11,
    fontWeight: "700",
  },
  approvalTextActive: {
    color: colors.teal,
  },
  serviceArea: {
    color: colors.muted,
    fontSize: 12,
  },
  statsRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: colors.line,
  },
  statCell: {
    flex: 1,
    gap: 4,
  },
  statDivider: {
    width: 1,
    height: 31,
    backgroundColor: colors.line,
    marginHorizontal: 18,
  },
  statLabel: {
    color: colors.muted,
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.8,
  },
  statValue: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "700",
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
  noticeCard: {
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
  noticeCardCompact: {
    maxWidth: undefined,
    alignSelf: "stretch",
    padding: 16,
  },
  noticeMark: {
    width: 9,
    height: 9,
    marginTop: 6,
    borderRadius: 5,
    backgroundColor: colors.amber,
  },
  noticeCopy: {
    flex: 1,
    gap: 5,
  },
  noticeTitle: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: "700",
  },
  noticeBody: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 19,
  },
  centerContent: {
    justifyContent: "center",
  },
});
