import { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
  useWindowDimensions,
} from "react-native";
import { useRouter } from "expo-router";

import { BrandMark } from "./BrandMark";
import { PrimaryButton } from "./PrimaryButton";
import { ScreenFrame } from "./ScreenFrame";
import { useAuth } from "../lib/auth";
import { ApiError, getApiConfigurationIssue, isApiConfigured } from "../lib/api";
import { colors } from "../lib/theme";

export function SignInScreen() {
  const router = useRouter();
  const { height } = useWindowDimensions();
  const compact = height < 700;
  const { signIn } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const configurationIssue = getApiConfigurationIssue();

  async function handleSignIn() {
    if (!isApiConfigured() || submitting) return;
    setError(null);
    setSubmitting(true);

    try {
      await signIn(username.trim(), password);
      setPassword("");
      router.replace("/(app)");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Sign in could not be completed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <ScreenFrame contentStyle={compact ? styles.contentCompact : styles.content}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <View style={[styles.hero, compact && styles.heroCompact]}>
          <View style={styles.brandRow}>
            <BrandMark size={compact ? 42 : 50} />
            <View>
              <Text style={styles.brandName}>Auto Aid</Text>
              <Text style={styles.brandCaption}>ROADSIDE SUPPORT</Text>
            </View>
          </View>
          <Text style={[styles.heroTitle, compact && styles.heroTitleCompact]}>
            Steady support, wherever the road takes you.
          </Text>
          <Text style={[styles.heroBody, compact && styles.heroBodyCompact]}>
            Sign in to stay close to your service requests.
          </Text>
          {!compact ? (
            <View style={styles.routeMark}>
              <View style={styles.routeLine} />
              <View style={styles.routeDot} />
              <View style={styles.routeDotEnd} />
            </View>
          ) : null}
        </View>

        <View style={[styles.formCard, compact && styles.formCardCompact]}>
          <View style={[styles.formHeading, compact && styles.formHeadingCompact]}>
            <Text style={styles.eyebrow}>WELCOME BACK</Text>
            <Text style={[styles.title, compact && styles.titleCompact]}>Sign in to your account</Text>
            <Text style={[styles.subtitle, compact && styles.subtitleCompact]}>
              Use the username and password for your Auto Aid account.
            </Text>
          </View>

          {configurationIssue ? (
            <View
              accessibilityRole="alert"
              style={[styles.configurationNotice, compact && styles.configurationNoticeCompact]}
            >
              <Text style={styles.noticeTitle}>API connection needed</Text>
              <Text style={[styles.noticeText, compact && styles.noticeTextCompact]}>
                {configurationIssue}
              </Text>
            </View>
          ) : null}

          <View style={[styles.fieldGroup, compact && styles.fieldGroupCompact]}>
            <Text style={styles.label}>Username</Text>
            <TextInput
              accessibilityLabel="Username"
              autoCapitalize="none"
              autoComplete="username"
              autoCorrect={false}
              onChangeText={setUsername}
              placeholder="Enter your username"
              placeholderTextColor={colors.muted}
              returnKeyType="next"
              style={[styles.input, compact && styles.inputCompact]}
              textContentType="username"
              value={username}
            />
          </View>

          <View style={[styles.fieldGroup, compact && styles.fieldGroupCompact]}>
            <Text style={styles.label}>Password</Text>
            <View style={styles.passwordWrap}>
              <TextInput
                accessibilityLabel="Password"
                autoCapitalize="none"
                autoComplete="current-password"
                onChangeText={setPassword}
                placeholder="Enter your password"
                placeholderTextColor={colors.muted}
                secureTextEntry={!passwordVisible}
                style={[styles.input, styles.passwordInput, compact && styles.inputCompact]}
                textContentType="password"
                value={password}
              />
              <Pressable
                accessibilityLabel={passwordVisible ? "Hide password" : "Show password"}
                accessibilityRole="button"
                onPress={() => setPasswordVisible((visible) => !visible)}
                style={styles.visibilityButton}
              >
                <Text style={styles.visibilityText}>{passwordVisible ? "Hide" : "Show"}</Text>
              </Pressable>
            </View>
          </View>

          {error ? (
            <Text accessibilityLiveRegion="polite" style={styles.error}>
              {error}
            </Text>
          ) : null}

          <PrimaryButton
            disabled={!username.trim() || !password || Boolean(configurationIssue)}
            label="Sign in"
            loading={submitting}
            onPress={() => void handleSignIn()}
            style={compact ? styles.submitCompact : styles.submit}
          />

          <Text style={[styles.footerNote, compact && styles.footerNoteCompact]}>
            Account registration is managed by Auto Aid. Sign in to create requests and follow assigned work.
          </Text>
        </View>
      </KeyboardAvoidingView>
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  content: {
    justifyContent: "center",
    paddingVertical: 30,
  },
  hero: {
    minHeight: 258,
    overflow: "hidden",
    position: "relative",
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    padding: 24,
    backgroundColor: colors.ink,
  },
  brandRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  brandName: {
    color: colors.white,
    fontSize: 18,
    fontWeight: "700",
  },
  brandCaption: {
    marginTop: 3,
    color: "#B9C8C8",
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 1.35,
  },
  heroTitle: {
    maxWidth: 360,
    marginTop: 28,
    color: colors.white,
    fontSize: 30,
    lineHeight: 36,
    fontWeight: "700",
  },
  heroBody: {
    marginTop: 9,
    color: "#D4DEDE",
    fontSize: 15,
    lineHeight: 22,
  },
  routeMark: {
    position: "absolute",
    right: 28,
    bottom: 24,
    width: 105,
    height: 22,
    justifyContent: "center",
  },
  routeLine: {
    height: 2,
    backgroundColor: colors.amber,
    opacity: 0.8,
  },
  routeDot: {
    position: "absolute",
    left: 2,
    width: 12,
    height: 12,
    borderRadius: 6,
    borderWidth: 3,
    borderColor: colors.amber,
    backgroundColor: colors.ink,
  },
  routeDotEnd: {
    position: "absolute",
    right: 2,
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: colors.amber,
  },
  formCard: {
    padding: 24,
    borderBottomLeftRadius: 28,
    borderBottomRightRadius: 28,
    gap: 18,
    backgroundColor: colors.paper,
    borderWidth: 1,
    borderTopWidth: 0,
    borderColor: colors.line,
  },
  formHeading: {
    gap: 7,
  },
  eyebrow: {
    color: colors.teal,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1.25,
  },
  title: {
    color: colors.ink,
    fontSize: 23,
    lineHeight: 29,
    fontWeight: "700",
  },
  subtitle: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 21,
  },
  configurationNotice: {
    gap: 5,
    borderRadius: 15,
    padding: 14,
    backgroundColor: colors.amberSoft,
    borderWidth: 1,
    borderColor: "#EBD09E",
  },
  noticeTitle: {
    color: colors.ink,
    fontSize: 14,
    fontWeight: "700",
  },
  noticeText: {
    color: colors.inkSoft,
    fontSize: 13,
    lineHeight: 19,
  },
  fieldGroup: {
    gap: 8,
  },
  label: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: "700",
  },
  input: {
    minHeight: 52,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: 14,
    paddingHorizontal: 15,
    color: colors.ink,
    backgroundColor: colors.white,
    fontSize: 15,
  },
  passwordWrap: {
    position: "relative",
    justifyContent: "center",
  },
  passwordInput: {
    paddingRight: 68,
  },
  visibilityButton: {
    position: "absolute",
    right: 12,
    minHeight: 42,
    justifyContent: "center",
    paddingHorizontal: 8,
  },
  visibilityText: {
    color: colors.teal,
    fontSize: 13,
    fontWeight: "700",
  },
  error: {
    color: colors.red,
    fontSize: 14,
    lineHeight: 20,
  },
  submit: {
    marginTop: 2,
  },
  footerNote: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
    textAlign: "center",
  },
  contentCompact: {
    justifyContent: "flex-start",
    paddingVertical: 8,
  },
  heroCompact: {
    minHeight: 0,
    borderTopLeftRadius: 22,
    borderTopRightRadius: 22,
    padding: 18,
  },
  heroTitleCompact: {
    maxWidth: 560,
    marginTop: 14,
    fontSize: 27,
    lineHeight: 32,
  },
  heroBodyCompact: {
    marginTop: 5,
    fontSize: 13,
    lineHeight: 18,
  },
  formCardCompact: {
    padding: 16,
    borderBottomLeftRadius: 22,
    borderBottomRightRadius: 22,
    gap: 11,
  },
  formHeadingCompact: {
    gap: 4,
  },
  titleCompact: {
    fontSize: 20,
    lineHeight: 25,
  },
  subtitleCompact: {
    fontSize: 12,
    lineHeight: 17,
  },
  configurationNoticeCompact: {
    gap: 3,
    padding: 10,
  },
  noticeTextCompact: {
    fontSize: 12,
    lineHeight: 16,
  },
  fieldGroupCompact: {
    gap: 5,
  },
  inputCompact: {
    minHeight: 44,
    borderRadius: 12,
    paddingHorizontal: 12,
    fontSize: 14,
  },
  submitCompact: {
    marginTop: 0,
    minHeight: 46,
    borderRadius: 14,
    paddingVertical: 8,
  },
  footerNoteCompact: {
    fontSize: 11,
    lineHeight: 15,
  },
});
