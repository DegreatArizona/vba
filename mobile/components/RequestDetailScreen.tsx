import { useRouter } from "expo-router";
import useSWR from "swr";
import { useState, type ReactNode } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { PrimaryButton } from "./PrimaryButton";
import { ApiError, getApiConfigurationIssue, getRequest, isApiConfigured, performMechanicRequestAction } from "../lib/api";
import { useAuth } from "../lib/auth";
import { colors } from "../lib/theme";
import type { MechanicRequestAction, ServiceRequest } from "../lib/types";

const progressStages = [
  "Request received",
  "Approved",
  "Mechanic assigned",
  "Service in progress",
  "Completed",
];

interface RequestDetailScreenProps {
  requestId: string;
}

function formatDate(value: string | null | undefined): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function displayValue(value: string | null | undefined): string | null {
  const trimmed = value?.trim();
  if (!trimmed || trimmed.toLowerCase() === "not available") return null;
  return trimmed;
}

function progressIndex(status: string): number {
  const value = status.toLowerCase();
  if (value.includes("release") || value.includes("complete") || value.includes("done")) return 4;
  if (value.includes("repair") || value.includes("progress")) return 3;
  if (value.includes("accept") || value.includes("assign")) return 2;
  if (value.includes("approv")) return 1;
  return 0;
}

interface MechanicActionInfo {
  action: MechanicRequestAction;
  label: string;
  description: string;
}

function mechanicActionForStatus(status: string): MechanicActionInfo | null {
  switch (status.toLowerCase()) {
    case "approved":
      return {
        action: "accept",
        label: "Accept assignment",
        description: "Confirm that you can take this assigned job.",
      };
    case "accepted":
      return {
        action: "start",
        label: "Start work",
        description: "Start the repair when you arrive at the vehicle.",
      };
    case "repairing":
      return {
        action: "complete",
        label: "Mark work complete",
        description: "Confirm that the requested service work is finished.",
      };
    default:
      return null;
  }
}

function mechanicStatusNote(status: string): string {
  const normalized = status.toLowerCase();
  if (normalized === "pending") return "This assignment is waiting for manager approval.";
  if (normalized === "done") {
    return "Work is complete. Payment and release are handled outside this mobile workflow.";
  }
  if (normalized === "released" || normalized === "cancelled") return "This job is closed.";
  return "No work action is available for this request status.";
}

function StatePanel({ title, body }: { title: string; body: string }) {
  return (
    <View style={styles.statePanel}>
      <Text style={styles.stateTitle}>{title}</Text>
      <Text style={styles.stateBody}>{body}</Text>
    </View>
  );
}

function DetailRow({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <View style={styles.detailRow}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text style={styles.detailValue}>{displayValue(value) ?? "Not provided"}</Text>
    </View>
  );
}

function ProgressCard({ status }: { status: string }) {
  const normalizedStatus = status.toLowerCase();
  const cancelled = normalizedStatus.includes("cancel");
  const currentIndex = progressIndex(status);

  return (
    <View style={styles.card}>
      <Text style={styles.sectionTitle}>Status path</Text>
      {cancelled ? (
        <StatePanel
          title="Request cancelled"
          body="This request is no longer active. Contact support if you need help with its outcome."
        />
      ) : (
        <View accessibilityLabel="Request progress" style={styles.progressList}>
          {progressStages.map((stage, index) => {
            const complete = index < currentIndex;
            const current = index === currentIndex;
            return (
              <View
                key={stage}
                accessibilityLabel={`${stage}, ${current ? "current" : complete ? "complete" : "upcoming"}`}
                style={styles.progressRow}
              >
                <View style={styles.progressRail}>
                  <View
                    style={[
                      styles.progressDot,
                      (complete || current) && styles.progressDotActive,
                      current && styles.progressDotCurrent,
                    ]}
                  />
                  {index < progressStages.length - 1 ? (
                    <View style={[styles.progressLine, complete && styles.progressLineActive]} />
                  ) : null}
                </View>
                <View style={styles.progressText}>
                  <Text style={[styles.progressLabel, (complete || current) && styles.progressLabelActive]}>
                    {stage}
                  </Text>
                  {current ? <Text style={styles.currentLabel}>CURRENT</Text> : null}
                </View>
              </View>
            );
          })}
        </View>
      )}
      <Text style={styles.statusNote}>
        Progress shows the current status only; event timestamps are not available in this view.
      </Text>
    </View>
  );
}

export function RequestDetailScreen({ requestId }: RequestDetailScreenProps) {
  const router = useRouter();
  const { user } = useAuth();
  const [actionInProgress, setActionInProgress] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const parsedId = /^\d+$/.test(requestId) ? Number(requestId) : Number.NaN;
  const validId = Number.isSafeInteger(parsedId) && parsedId > 0;
  const canReadRequests = Boolean(
    user?.is_email_verified && (user.role === "driver" || user.is_approved),
  );
  const configurationIssue = getApiConfigurationIssue();
  const key = validId && canReadRequests && isApiConfigured()
    ? `/api/v1/requests/${parsedId}/`
    : null;
  const { data, error, isLoading, mutate } = useSWR<ServiceRequest>(
    key,
    () => getRequest(parsedId),
    { revalidateOnFocus: false, revalidateOnReconnect: false, shouldRetryOnError: false },
  );

  async function handleMechanicAction(action: MechanicRequestAction) {
    setActionError(null);
    setActionInProgress(true);
    try {
      await performMechanicRequestAction(parsedId, action);
      await mutate();
    } catch (caught) {
      setActionError(caught instanceof ApiError ? caught.message : "The job update could not be completed.");
    } finally {
      setActionInProgress(false);
    }
  }

  const page = (content: ReactNode) => (
    <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
      <View style={styles.container}>
        <Pressable
          accessibilityLabel="Back to requests"
          accessibilityRole="button"
          onPress={() => router.back()}
          style={styles.backButton}
        >
          <Text style={styles.backArrow}>‹</Text>
          <Text style={styles.backLabel}>All requests</Text>
        </Pressable>
        {content}
      </View>
    </ScrollView>
  );

  if (!user) return null;
  if (!user.is_email_verified) {
    return page(
      <StatePanel
        title="Verify your email first"
        body="Request details are available after your email address is verified."
      />,
    );
  }
  if (user.role !== "driver" && !user.is_approved) {
    return page(
      <StatePanel
        title="Profile awaiting approval"
        body="Request details will be available after your Auto Aid profile is approved."
      />,
    );
  }
  if (!validId) return page(<StatePanel title="Request unavailable" body="This request link is not valid." />);
  if (configurationIssue) return page(<StatePanel title="Connect the service API" body={configurationIssue} />);
  if (isLoading) {
    return page(
      <View style={styles.loadingCard}>
        <ActivityIndicator color={colors.teal} />
        <Text style={styles.loadingText}>Loading request details</Text>
      </View>,
    );
  }
  if (error) {
    const notFound = error instanceof ApiError && error.status === 404;
    const title = notFound
      ? "Request unavailable"
      : error instanceof ApiError && error.status === 401
        ? "Session expired"
        : "Could not load request";
    return page(
      <View style={styles.statePanel}>
        <Text style={styles.stateTitle}>{title}</Text>
        <Text style={styles.stateBody}>
          {notFound ? "This request is not available to your account." : error.message || "Check your connection and try again."}
        </Text>
        <PrimaryButton label="Try again" onPress={() => void mutate()} style={styles.retryButton} />
      </View>,
    );
  }
  if (!data) return page(<StatePanel title="Request unavailable" body="No request details were returned." />);

  const status = data.status?.replace(/[_-]/g, " ").trim() || "Status unavailable";
  const statusCancelled = status.toLowerCase().includes("cancel");
  const statusColor = statusCancelled ? colors.red : colors.teal;
  const location = [data.location, data.state].filter(Boolean).join(", ");
  const vehicle = [data.vehicle_name, data.vehicle_no].filter(Boolean).join(" · ");
  const submitted = formatDate(data.date);
  const expectedCompletion = formatDate(data.estimated_completion_date);
  const mechanicLocation = displayValue(data.mechanic_location);
  const eta = displayValue(data.eta);

  return page(
    <>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>SERVICE REQUEST</Text>
        <Text style={styles.title}>Request #{data.id}</Text>
        <Text style={styles.category}>{data.category || "Vehicle assistance"}</Text>
        <View style={[styles.statusBadge, { backgroundColor: statusCancelled ? colors.redSoft : colors.tealSoft }]}>
          <Text style={[styles.statusText, { color: statusColor }]}>{status}</Text>
        </View>
        {submitted ? <Text style={styles.submitted}>Submitted {submitted}</Text> : null}
      </View>

      <ProgressCard status={status} />

      {user.role === "mechanic" ? (
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Work actions</Text>
          <Text style={styles.actionDescription}>
            {mechanicActionForStatus(status)?.description ?? mechanicStatusNote(status)}
          </Text>
          {actionError ? (
            <Text accessibilityRole="alert" style={styles.actionError}>{actionError}</Text>
          ) : null}
          {mechanicActionForStatus(status) ? (
            <PrimaryButton
              label={mechanicActionForStatus(status)?.label ?? "Update job"}
              loading={actionInProgress}
              disabled={actionInProgress}
              onPress={() => {
                const action = mechanicActionForStatus(status);
                if (action) void handleMechanicAction(action.action);
              }}
            />
          ) : null}
        </View>
      ) : null}

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Vehicle and location</Text>
        <DetailRow label="Vehicle" value={vehicle} />
        <DetailRow label="Location" value={location} />
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Issue details</Text>
        <Text style={styles.issueText}>{displayValue(data.problem_description) ?? "No issue description was provided."}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Service updates</Text>
        <DetailRow label="Mechanic location" value={mechanicLocation} />
        <DetailRow label="Estimated arrival" value={eta} />
        <DetailRow label="Estimated completion" value={expectedCompletion} />
        {!mechanicLocation && !eta && !expectedCompletion ? (
          <Text style={styles.emptyUpdate}>No mechanic location or timing has been shared yet.</Text>
        ) : null}
      </View>
    </>,
  );
}

const styles = StyleSheet.create({
  scrollContent: {
    flexGrow: 1,
    backgroundColor: colors.canvas,
    paddingHorizontal: 20,
    paddingVertical: 18,
  },
  container: {
    width: "100%",
    maxWidth: 720,
    alignSelf: "center",
    gap: 16,
  },
  backButton: {
    alignSelf: "flex-start",
    minHeight: 42,
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 10,
    borderRadius: 12,
  },
  backArrow: {
    color: colors.ink,
    fontSize: 28,
    lineHeight: 30,
  },
  backLabel: {
    color: colors.inkSoft,
    fontSize: 14,
    fontWeight: "600",
  },
  header: {
    padding: 22,
    gap: 9,
    borderRadius: 22,
    backgroundColor: colors.ink,
  },
  eyebrow: {
    color: "#B8D8D0",
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1.4,
  },
  title: {
    color: colors.paper,
    fontSize: 28,
    lineHeight: 34,
    fontWeight: "800",
  },
  category: {
    color: "#D8E2DD",
    fontSize: 15,
    fontWeight: "600",
  },
  statusBadge: {
    alignSelf: "flex-start",
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  statusText: {
    fontSize: 12,
    fontWeight: "700",
    textTransform: "capitalize",
  },
  submitted: {
    color: "#D8E2DD",
    fontSize: 12,
  },
  card: {
    padding: 20,
    gap: 16,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.paper,
  },
  sectionTitle: {
    color: colors.ink,
    fontSize: 17,
    fontWeight: "700",
  },
  progressList: {
    gap: 0,
  },
  progressRow: {
    minHeight: 43,
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
  },
  progressRail: {
    width: 16,
    height: 43,
    alignItems: "center",
  },
  progressDot: {
    width: 11,
    height: 11,
    marginTop: 3,
    zIndex: 1,
    borderRadius: 999,
    borderWidth: 2,
    borderColor: colors.line,
    backgroundColor: colors.paper,
  },
  progressDotActive: {
    borderColor: colors.teal,
    backgroundColor: colors.teal,
  },
  progressDotCurrent: {
    width: 15,
    height: 15,
    marginTop: 1,
    borderWidth: 3,
    borderColor: colors.tealSoft,
  },
  progressLine: {
    position: "absolute",
    top: 15,
    bottom: -1,
    width: 2,
    backgroundColor: colors.line,
  },
  progressLineActive: {
    backgroundColor: colors.teal,
  },
  progressText: {
    minHeight: 27,
    flex: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 12,
  },
  progressLabel: {
    color: colors.muted,
    fontSize: 14,
  },
  progressLabelActive: {
    color: colors.inkSoft,
    fontWeight: "600",
  },
  currentLabel: {
    color: colors.teal,
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.8,
  },
  statusNote: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
  },
  detailRow: {
    gap: 4,
    paddingVertical: 9,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
  },
  detailLabel: {
    color: colors.muted,
    fontSize: 12,
  },
  detailValue: {
    color: colors.inkSoft,
    fontSize: 14,
    lineHeight: 20,
    fontWeight: "600",
  },
  issueText: {
    color: colors.inkSoft,
    fontSize: 14,
    lineHeight: 22,
  },
  actionDescription: {
    color: colors.inkSoft,
    fontSize: 14,
    lineHeight: 21,
  },
  actionError: {
    color: colors.red,
    fontSize: 13,
    lineHeight: 19,
  },
  emptyUpdate: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 20,
  },
  statePanel: {
    padding: 20,
    gap: 8,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.paper,
  },
  stateTitle: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "700",
  },
  stateBody: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 20,
  },
  loadingCard: {
    minHeight: 140,
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: 12,
    borderRadius: 18,
    backgroundColor: colors.paper,
  },
  loadingText: {
    color: colors.muted,
    fontSize: 14,
  },
  retryButton: {
    marginTop: 8,
  },
});
