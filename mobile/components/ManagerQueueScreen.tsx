import { useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import useSWRInfinite from "swr/infinite";

import { BrandMark } from "./BrandMark";
import { PrimaryButton } from "./PrimaryButton";
import { ScreenFrame } from "./ScreenFrame";
import { ApiError, claimManagerRequest, getApiConfigurationIssue, getManagerMechanicPage, getManagerQueuePage, isApiConfigured } from "../lib/api";
import { useAuth } from "../lib/auth";
import { colors } from "../lib/theme";
import type { ManagerMechanicPage, ManagerMechanicSummary, ManagerQueuePage, ManagerQueueRequest } from "../lib/types";

export function ManagerQueueScreen() {
  const { user } = useAuth();
  const canReadQueue = Boolean(
    user?.role === "manager" && user.is_email_verified && user.is_approved && isApiConfigured(),
  );
  const [selectedMechanics, setSelectedMechanics] = useState<Record<number, number>>({});
  const [claimingRequestId, setClaimingRequestId] = useState<number | null>(null);
  const [claimErrors, setClaimErrors] = useState<Record<number, string>>({});
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const getQueueKey = (pageIndex: number, previousPage: ManagerQueuePage | null) => {
    if (!canReadQueue) return null;
    if (pageIndex > 0 && !previousPage?.next) return null;
    return String(pageIndex + 1);
  };
  const {
    data: queuePages,
    error: queueError,
    isLoading: isQueueLoading,
    isValidating: isQueueValidating,
    size: queueSize,
    setSize: setQueueSize,
    mutate: refreshQueue,
  } = useSWRInfinite<ManagerQueuePage>(getQueueKey, (page) => getManagerQueuePage(Number(page)), {
    revalidateOnFocus: true,
    revalidateOnReconnect: true,
    refreshInterval: 30000,
    shouldRetryOnError: false,
  });

  const getMechanicKey = (pageIndex: number, previousPage: ManagerMechanicPage | null) => {
    if (!canReadQueue) return null;
    if (pageIndex > 0 && !previousPage?.next) return null;
    return String(pageIndex + 1);
  };
  const {
    data: mechanicPages,
    error: mechanicError,
    isLoading: areMechanicsLoading,
    isValidating: areMechanicsValidating,
    size: mechanicSize,
    setSize: setMechanicSize,
    mutate: refreshMechanics,
  } = useSWRInfinite<ManagerMechanicPage>(
    getMechanicKey,
    (page) => getManagerMechanicPage(Number(page), 100),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      shouldRetryOnError: false,
    },
  );

  const requests = useMemo(() => queuePages?.flatMap((page) => page.results) ?? [], [queuePages]);
  const team = useMemo(() => mechanicPages?.flatMap((page) => page.results) ?? [], [mechanicPages]);
  const eligibleMechanics = useMemo(() => team.filter((mechanic) => mechanic.can_be_assigned), [team]);
  const lastQueuePage = queuePages?.[queuePages.length - 1];
  const lastMechanicPage = mechanicPages?.[mechanicPages.length - 1];
  const configurationIssue = getApiConfigurationIssue();

  if (!user) return null;

  if (user.role !== "manager") {
    return (
      <ScreenFrame contentStyle={styles.centerContent}>
        <NoticeCard title="Managers only" body="The request queue is available to manager accounts." />
      </ScreenFrame>
    );
  }

  if (!user.is_email_verified) {
    return (
      <ScreenFrame contentStyle={styles.centerContent}>
        <NoticeCard title="Verify your email first" body="Queue access is available after your email is verified." />
      </ScreenFrame>
    );
  }

  if (!user.is_approved) {
    return (
      <ScreenFrame contentStyle={styles.centerContent}>
        <NoticeCard title="Manager approval pending" body="The regional queue will appear after your profile is approved." />
      </ScreenFrame>
    );
  }

  async function handleClaim(request: ManagerQueueRequest, mechanic: ManagerMechanicSummary) {
    if (claimingRequestId !== null) return;
    setClaimingRequestId(request.id);
    setClaimErrors((current) => ({ ...current, [request.id]: "" }));
    setSuccessMessage(null);

    try {
      await claimManagerRequest(request.id, mechanic.id);
      setSuccessMessage(`Request #${request.id} is accepted and assigned to ${mechanic.full_name}.`);
      setSelectedMechanics((current) => {
        const next = { ...current };
        delete next[request.id];
        return next;
      });
      await Promise.all([refreshQueue(), refreshMechanics()]);
    } catch (caught) {
      setClaimErrors((current) => ({
        ...current,
        [request.id]: caught instanceof ApiError ? caught.message : "The request could not be claimed. Try again.",
      }));
    } finally {
      setClaimingRequestId(null);
    }
  }

  return (
    <ScrollView
      contentContainerStyle={styles.scrollContent}
      refreshControl={
        <RefreshControl
          colors={[colors.teal]}
          onRefresh={() => void Promise.all([refreshQueue(), refreshMechanics()])}
          refreshing={Boolean((isQueueValidating || areMechanicsValidating) && (queuePages || mechanicPages))}
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
          <View style={styles.roleBadge}><Text style={styles.roleBadgeText}>Manager</Text></View>
        </View>

        <View style={styles.heading}>
          <Text style={styles.eyebrow}>NEW SERVICE REQUESTS</Text>
          <Text style={styles.title}>Regional queue</Text>
          <Text style={styles.description}>
            Pending requests are visible to approved managers in the same state. Claiming accepts the request and assigns it to one of your eligible mechanics.
          </Text>
        </View>

        <View style={styles.privacyNote}>
          <Text style={styles.privacyTitle}>State-scoped access</Text>
          <Text style={styles.privacyText}>
            Queue cards omit driver contact and billing details. A manager can hold one active assignment at a time; the server rechecks availability when you claim.
          </Text>
        </View>

        {configurationIssue ? (
          <NoticeCard title="Connect the service API" body={configurationIssue} compact />
        ) : queueError ? (
          <NoticeCard
            title={queueError instanceof ApiError && queueError.status === 401 ? "Session expired" : "Could not load the regional queue"}
            body={queueError.message ?? "Check your connection and try again."}
            compact
          />
        ) : isQueueLoading ? (
          <View style={styles.loadingCard}>
            <ActivityIndicator color={colors.teal} />
            <Text style={styles.loadingText}>Loading state-matched requests</Text>
          </View>
        ) : (
          <View style={styles.requestList}>
            {successMessage ? <Text accessibilityRole="status" style={styles.successMessage}>{successMessage}</Text> : null}
            {mechanicError ? (
              <NoticeCard title="Could not load your mechanics" body={mechanicError.message ?? "Refresh to try again."} compact />
            ) : null}
            {!areMechanicsLoading && !mechanicError && eligibleMechanics.length === 0 ? (
              <NoticeCard
                title="No eligible mechanics"
                body="Only approved, verified mechanics linked to your manager profile and without an active assignment can receive a request."
                compact
              />
            ) : null}
            {requests.length ? (
              <View style={styles.sectionHeader}>
                <View>
                  <Text style={styles.sectionTitle}>Available to claim</Text>
                  <Text style={styles.sectionCaption}>{queuePages?.[0]?.count ?? requests.length} pending requests in your state</Text>
                </View>
                {isQueueValidating ? <ActivityIndicator color={colors.teal} /> : null}
              </View>
            ) : (
              <NoticeCard
                title="No requests in your state"
                body="New pending driver requests will appear here when their state matches your manager profile."
                compact
              />
            )}
            {requests.map((request) => (
              <QueueRequestCard
                key={request.id}
                request={request}
                mechanics={eligibleMechanics}
                selectedMechanicId={selectedMechanics[request.id] ?? null}
                onSelectMechanic={(mechanicId) => {
                  setSelectedMechanics((current) => ({ ...current, [request.id]: mechanicId }));
                  setClaimErrors((current) => ({ ...current, [request.id]: "" }));
                }}
                onClaim={(mechanic) => void handleClaim(request, mechanic)}
                loading={claimingRequestId === request.id}
                disabled={claimingRequestId !== null || areMechanicsLoading || Boolean(mechanicError)}
                error={claimErrors[request.id] || null}
              />
            ))}
            {lastQueuePage?.next ? (
              <PrimaryButton
                disabled={isQueueValidating}
                label="Load more requests"
                loading={isQueueValidating && queueSize > (queuePages?.length ?? 0)}
                onPress={() => void setQueueSize(queueSize + 1)}
              />
            ) : null}
            {lastMechanicPage?.next ? (
              <Pressable
                accessibilityRole="button"
                disabled={areMechanicsValidating}
                onPress={() => void setMechanicSize(mechanicSize + 1)}
                style={styles.moreMechanicsButton}
              >
                <Text style={styles.moreMechanicsText}>
                  {areMechanicsValidating && mechanicSize > (mechanicPages?.length ?? 0) ? "Loading mechanics…" : "Load more team mechanics"}
                </Text>
              </Pressable>
            ) : null}
          </View>
        )}
      </View>
    </ScrollView>
  );
}

function QueueRequestCard({
  request,
  mechanics,
  selectedMechanicId,
  onSelectMechanic,
  onClaim,
  loading,
  disabled,
  error,
}: {
  request: ManagerQueueRequest;
  mechanics: ManagerMechanicSummary[];
  selectedMechanicId: number | null;
  onSelectMechanic: (mechanicId: number) => void;
  onClaim: (mechanic: ManagerMechanicSummary) => void;
  loading: boolean;
  disabled: boolean;
  error: string | null;
}) {
  const selectedMechanic = mechanics.find((mechanic) => mechanic.id === selectedMechanicId);

  return (
    <View style={styles.requestCard}>
      <View style={styles.requestHeader}>
        <View style={styles.requestTitleBlock}>
          <Text style={styles.requestCategory}>{request.category}</Text>
          <Text style={styles.requestTitle}>{request.vehicle_name}</Text>
          <Text style={styles.vehiclePlate}>{request.vehicle_no}</Text>
        </View>
        <View style={styles.pendingBadge}><Text style={styles.pendingText}>Pending</Text></View>
      </View>

      <View style={styles.requestDetails}>
        <Text style={styles.detailLabel}>ISSUE</Text>
        <Text style={styles.detailText}>{request.problem_description}</Text>
        <Text style={styles.locationText}>{request.location}, {request.state}</Text>
        <Text style={styles.dateText}>{formatRequestDate(request.date)}</Text>
      </View>

      {mechanics.length ? (
        <View style={styles.assignmentGroup}>
          <Text style={styles.assignmentLabel}>Assign to an eligible mechanic</Text>
          <View accessibilityLabel={`Mechanic selection for request ${request.id}`} accessibilityRole="radiogroup" style={styles.mechanicChoices}>
            {mechanics.map((mechanic) => {
              const selected = mechanic.id === selectedMechanicId;
              return (
                <Pressable
                  key={mechanic.id}
                  accessibilityLabel={mechanic.full_name}
                  accessibilityRole="radio"
                  accessibilityState={{ checked: selected, disabled: disabled || loading }}
                  disabled={disabled || loading}
                  onPress={() => onSelectMechanic(mechanic.id)}
                  style={[styles.mechanicChoice, selected && styles.mechanicChoiceSelected, (disabled || loading) && styles.disabledChoice]}
                >
                  <Text style={[styles.mechanicChoiceText, selected && styles.mechanicChoiceTextSelected]}>{mechanic.full_name}</Text>
                  <Text style={[styles.mechanicAvailability, selected && styles.mechanicAvailabilitySelected]}>
                    {mechanic.active_request_count === 0 ? "Available" : "Active job"}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>
      ) : null}

      {error ? <Text accessibilityRole="alert" style={styles.errorText}>{error}</Text> : null}
      <PrimaryButton
        disabled={disabled || !selectedMechanic || loading}
        label="Claim & assign"
        loading={loading}
        onPress={() => selectedMechanic && onClaim(selectedMechanic)}
      />
    </View>
  );
}

function formatRequestDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Date unavailable";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
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
  container: { width: "100%", maxWidth: 720, alignSelf: "center", gap: 20 },
  topBar: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  brand: { flexDirection: "row", alignItems: "center", gap: 10 },
  brandName: { color: colors.ink, fontSize: 16, fontWeight: "700" },
  brandCaption: { marginTop: 2, color: colors.muted, fontSize: 9, fontWeight: "700", letterSpacing: 1.1 },
  roleBadge: { borderRadius: 999, paddingHorizontal: 13, paddingVertical: 8, backgroundColor: colors.tealSoft },
  roleBadgeText: { color: colors.teal, fontSize: 12, fontWeight: "700" },
  heading: { gap: 7, marginTop: 6 },
  eyebrow: { color: colors.teal, fontSize: 11, fontWeight: "700", letterSpacing: 1.05 },
  title: { color: colors.ink, fontSize: 30, lineHeight: 36, fontWeight: "700" },
  description: { color: colors.muted, fontSize: 14, lineHeight: 21 },
  privacyNote: { gap: 5, borderRadius: 16, padding: 16, backgroundColor: colors.tealSoft },
  privacyTitle: { color: colors.ink, fontSize: 14, fontWeight: "700" },
  privacyText: { color: colors.inkSoft, fontSize: 12, lineHeight: 18 },
  requestList: { gap: 12 },
  sectionHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 2 },
  sectionTitle: { color: colors.ink, fontSize: 18, fontWeight: "700" },
  sectionCaption: { marginTop: 4, color: colors.muted, fontSize: 12 },
  requestCard: { gap: 16, padding: 17, borderRadius: 18, backgroundColor: colors.paper, borderWidth: 1, borderColor: colors.line },
  requestHeader: { flexDirection: "row", alignItems: "flex-start", justifyContent: "space-between", gap: 12 },
  requestTitleBlock: { flex: 1, gap: 4 },
  requestCategory: { color: colors.teal, fontSize: 11, fontWeight: "700", letterSpacing: 0.7, textTransform: "uppercase" },
  requestTitle: { color: colors.ink, fontSize: 17, fontWeight: "700" },
  vehiclePlate: { color: colors.muted, fontSize: 12, fontWeight: "600" },
  pendingBadge: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 6, backgroundColor: colors.amberSoft },
  pendingText: { color: colors.inkSoft, fontSize: 11, fontWeight: "700" },
  requestDetails: { gap: 6, borderTopWidth: 1, borderTopColor: colors.line, paddingTop: 13 },
  detailLabel: { color: colors.muted, fontSize: 10, fontWeight: "700", letterSpacing: 0.8 },
  detailText: { color: colors.inkSoft, fontSize: 13, lineHeight: 19 },
  locationText: { color: colors.ink, fontSize: 13, fontWeight: "600" },
  dateText: { color: colors.muted, fontSize: 11 },
  assignmentGroup: { gap: 9 },
  assignmentLabel: { color: colors.ink, fontSize: 13, fontWeight: "700" },
  mechanicChoices: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  mechanicChoice: { minHeight: 52, justifyContent: "center", gap: 3, borderWidth: 1, borderColor: colors.line, borderRadius: 13, paddingHorizontal: 12, paddingVertical: 8, backgroundColor: colors.white },
  mechanicChoiceSelected: { borderColor: colors.teal, backgroundColor: colors.tealSoft },
  disabledChoice: { opacity: 0.55 },
  mechanicChoiceText: { color: colors.inkSoft, fontSize: 12, fontWeight: "700" },
  mechanicChoiceTextSelected: { color: colors.teal },
  mechanicAvailability: { color: colors.muted, fontSize: 10 },
  mechanicAvailabilitySelected: { color: colors.teal },
  errorText: { color: colors.red, fontSize: 12, lineHeight: 18 },
  successMessage: { color: colors.teal, fontSize: 13, lineHeight: 19, fontWeight: "700", padding: 13, borderRadius: 14, backgroundColor: colors.tealSoft },
  moreMechanicsButton: { alignSelf: "center", minHeight: 44, justifyContent: "center", paddingHorizontal: 12 },
  moreMechanicsText: { color: colors.teal, fontSize: 13, fontWeight: "700" },
  loadingCard: { minHeight: 110, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 12, borderRadius: 18, backgroundColor: colors.paper, borderWidth: 1, borderColor: colors.line },
  loadingText: { color: colors.muted, fontSize: 14 },
  noticeCard: { width: "100%", maxWidth: 520, alignSelf: "center", flexDirection: "row", gap: 13, padding: 20, borderRadius: 20, backgroundColor: colors.paper, borderWidth: 1, borderColor: colors.line },
  noticeCardCompact: { maxWidth: undefined, alignSelf: "stretch", padding: 16 },
  noticeMark: { width: 9, height: 9, marginTop: 6, borderRadius: 5, backgroundColor: colors.amber },
  noticeCopy: { flex: 1, gap: 5 },
  noticeTitle: { color: colors.ink, fontSize: 15, fontWeight: "700" },
  noticeBody: { color: colors.muted, fontSize: 13, lineHeight: 19 },
  centerContent: { justifyContent: "center" },
});
