import { StyleSheet, Text, View } from "react-native";

import { BrandMark } from "./BrandMark";
import { PrimaryButton } from "./PrimaryButton";
import { ScreenFrame } from "./ScreenFrame";
import { useAuth } from "../lib/auth";
import { colors } from "../lib/theme";

export function AccountScreen() {
  const { user, signOut } = useAuth();
  if (!user) return null;

  const fullName = [user.first_name, user.last_name].filter(Boolean).join(" ") || user.username;
  const profileStatus = !user.is_email_verified
    ? "Email verification required"
    : user.role === "driver" || user.is_approved
      ? "Account ready"
      : "Awaiting approval";

  return (
    <ScreenFrame>
      <View style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.eyebrow}>YOUR ACCOUNT</Text>
          <Text style={styles.title}>Profile</Text>
          <Text style={styles.subtitle}>Your Auto Aid sign-in and account status.</Text>
        </View>

        <View style={styles.profileCard}>
          <View style={styles.identity}>
            <BrandMark size={58} />
            <View style={styles.identityCopy}>
              <Text style={styles.name}>{fullName}</Text>
              <Text style={styles.role}>{user.role}</Text>
            </View>
          </View>
          <View style={styles.divider} />
          <DetailRow label="Username" value={user.username} />
          <DetailRow label="Email" value={user.email || "Not provided"} />
          <DetailRow label="Account status" value={profileStatus} />
        </View>

        <View style={styles.privacyNote}>
          <Text style={styles.privacyTitle}>Session protection</Text>
          <Text style={styles.privacyBody}>
            On iOS and Android, sign-in tokens are stored in the device keychain or keystore. The browser preview keeps them in memory only.
          </Text>
        </View>

        <PrimaryButton label="Sign out" onPress={() => void signOut()} style={styles.signOut} />
      </View>
    </ScreenFrame>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.detailRow}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text selectable style={styles.detailValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  page: {
    width: "100%",
    maxWidth: 680,
    alignSelf: "center",
    gap: 20,
  },
  header: {
    gap: 7,
  },
  eyebrow: {
    color: colors.teal,
    fontSize: 11,
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
    fontSize: 14,
    lineHeight: 21,
  },
  profileCard: {
    padding: 19,
    gap: 16,
    borderRadius: 20,
    backgroundColor: colors.paper,
    borderWidth: 1,
    borderColor: colors.line,
  },
  identity: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
  },
  identityCopy: {
    flex: 1,
    gap: 4,
  },
  name: {
    color: colors.ink,
    fontSize: 17,
    fontWeight: "700",
  },
  role: {
    color: colors.teal,
    fontSize: 13,
    fontWeight: "700",
    textTransform: "capitalize",
  },
  divider: {
    height: 1,
    backgroundColor: colors.line,
  },
  detailRow: {
    gap: 4,
  },
  detailLabel: {
    color: colors.muted,
    fontSize: 12,
  },
  detailValue: {
    color: colors.ink,
    fontSize: 14,
    fontWeight: "600",
  },
  privacyNote: {
    gap: 6,
    padding: 16,
    borderRadius: 16,
    backgroundColor: colors.tealSoft,
  },
  privacyTitle: {
    color: colors.teal,
    fontSize: 14,
    fontWeight: "700",
  },
  privacyBody: {
    color: colors.inkSoft,
    fontSize: 13,
    lineHeight: 19,
  },
  signOut: {
    backgroundColor: colors.ink,
  },
});
