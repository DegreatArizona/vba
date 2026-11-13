import { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
  type TextInputProps,
} from "react-native";
import { useRouter } from "expo-router";

import { BrandMark } from "./BrandMark";
import { PrimaryButton } from "./PrimaryButton";
import { ScreenFrame } from "./ScreenFrame";
import {
  ApiError,
  getApiConfigurationIssue,
  isApiConfigured,
  registerAccount,
  resendVerificationEmail,
} from "../lib/api";
import { colors } from "../lib/theme";
import type { MechanicService, MobileRegistrationInput, RegistrationRole } from "../lib/types";

const mechanicServices: MechanicService[] = [
  "Tire Repair",
  "Towing Service",
  "Battery Jumpstart",
  "Electrical Issues",
  "Engine Repair",
  "Bodywork/Collision Repair",
  "Other Repair Service",
  "General Mechanics/All Services",
];

const initialFields = {
  first_name: "",
  last_name: "",
  username: "",
  email: "",
  password: "",
  password_confirm: "",
  mobile: "",
  address: "",
  license_no: "",
  vehicle_model: "",
  state: "",
  local_government: "",
  union_name: "",
  union_location: "",
};

export function RegisterScreen() {
  const router = useRouter();
  const [role, setRole] = useState<RegistrationRole>("driver");
  const [fields, setFields] = useState(initialFields);
  const [services, setServices] = useState<MechanicService[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [resendNotice, setResendNotice] = useState<string | null>(null);
  const configurationIssue = getApiConfigurationIssue();
  const isMechanic = role === "mechanic";
  const formIsValid = Boolean(
    fields.first_name.trim() &&
      fields.last_name.trim() &&
      fields.username.trim() &&
      fields.email.trim() &&
      fields.mobile.trim() &&
      fields.password.length >= 8 &&
      fields.password_confirm &&
      fields.password === fields.password_confirm &&
      (!isMechanic || (fields.state.trim() && fields.local_government.trim() && services.length > 0)),
  );

  function updateField(field: keyof typeof initialFields, value: string) {
    setFields((current) => ({ ...current, [field]: value }));
  }

  function toggleService(service: MechanicService) {
    setServices((current) =>
      current.includes(service) ? current.filter((item) => item !== service) : [...current, service],
    );
  }

  async function handleRegister() {
    if (!formIsValid || configurationIssue || submitting) return;
    setError(null);
    setResendNotice(null);
    setSubmitting(true);

    const input: MobileRegistrationInput = {
      ...fields,
      role,
    };
    if (isMechanic) input.services = services;

    try {
      const result = await registerAccount(input);
      setSuccess(result.detail);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Your account could not be created.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResendVerification() {
    if (!isApiConfigured() || resending) return;
    setError(null);
    setResendNotice(null);
    setResending(true);
    try {
      const result = await resendVerificationEmail(fields.email.trim());
      setResendNotice(result.detail);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "The verification email could not be requested.");
    } finally {
      setResending(false);
    }
  }

  return (
    <ScreenFrame contentStyle={styles.screenContent}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <View style={styles.card}>
          <View style={styles.brandRow}>
            <BrandMark size={44} />
            <View>
              <Text style={styles.brandName}>Auto Aid</Text>
              <Text style={styles.brandCaption}>ROADSIDE SUPPORT</Text>
            </View>
          </View>

          {success ? (
            <View style={styles.successContent}>
              <Text style={styles.eyebrow}>ONE LAST STEP</Text>
              <Text style={styles.title}>Check your email</Text>
              <Text style={styles.body}>{success}</Text>
              <Text style={styles.emailAddress}>{fields.email.trim()}</Text>
              {role === "mechanic" ? (
                <Text style={styles.body}>Mechanic work features become available after account verification and Auto Aid approval.</Text>
              ) : (
                <Text style={styles.body}>Verify your email before creating a service request.</Text>
              )}
              {resendNotice ? <Text accessibilityRole="alert" style={styles.successNotice}>{resendNotice}</Text> : null}
              {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
              <PrimaryButton
                label="Resend verification email"
                loading={resending}
                onPress={() => void handleResendVerification()}
                disabled={Boolean(configurationIssue)}
                style={styles.submitButton}
              />
              <Pressable accessibilityRole="button" onPress={() => router.replace("/sign-in")} style={styles.textLinkButton}>
                <Text style={styles.textLink}>Back to sign in</Text>
              </Pressable>
            </View>
          ) : (
            <View style={styles.formContent}>
              <Text style={styles.eyebrow}>CREATE YOUR ACCOUNT</Text>
              <Text style={styles.title}>Join Auto Aid</Text>
              <Text style={styles.body}>Create a driver or mechanic account. Manager access is invitation-only.</Text>

              <View accessibilityRole="radiogroup" style={styles.roleChoices}>
                {(["driver", "mechanic"] as const).map((choice) => {
                  const selected = choice === role;
                  return (
                    <Pressable
                      key={choice}
                      accessibilityRole="radio"
                      accessibilityState={{ checked: selected, selected }}
                      aria-checked={selected}
                      onPress={() => setRole(choice)}
                      style={[styles.roleChoice, selected && styles.roleChoiceSelected]}
                    >
                      <Text style={[styles.roleChoiceText, selected && styles.roleChoiceTextSelected]}>
                        {choice === "driver" ? "Driver" : "Mechanic"}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>

              {configurationIssue ? (
                <View accessibilityRole="alert" style={styles.configurationNotice}>
                  <Text style={styles.noticeTitle}>API connection needed</Text>
                  <Text style={styles.noticeText}>{configurationIssue}</Text>
                </View>
              ) : null}

              <View style={styles.fieldGrid}>
                <FormField label="First name" value={fields.first_name} onChangeText={(value) => updateField("first_name", value)} placeholder="First name" autoCapitalize="words" autoComplete="given-name" />
                <FormField label="Last name" value={fields.last_name} onChangeText={(value) => updateField("last_name", value)} placeholder="Last name" autoCapitalize="words" autoComplete="family-name" />
                <FormField label="Username" value={fields.username} onChangeText={(value) => updateField("username", value)} placeholder="Choose a username" autoComplete="username-new" />
                <FormField label="Email address" value={fields.email} onChangeText={(value) => updateField("email", value)} placeholder="you@example.com" keyboardType="email-address" autoComplete="email" />
                <FormField label="Mobile number" value={fields.mobile} onChangeText={(value) => updateField("mobile", value)} placeholder="Your contact number" keyboardType="phone-pad" autoComplete="tel" />
                <FormField label="Password" value={fields.password} onChangeText={(value) => updateField("password", value)} placeholder="At least 8 characters" secureTextEntry autoComplete="new-password" />
                <FormField label="Confirm password" value={fields.password_confirm} onChangeText={(value) => updateField("password_confirm", value)} placeholder="Enter your password again" secureTextEntry autoComplete="new-password" />
                <FormField label="Address (optional)" value={fields.address} onChangeText={(value) => updateField("address", value)} placeholder="Street or neighborhood" autoComplete="street-address" />
              </View>

              {isMechanic ? (
                <View style={styles.mechanicFields}>
                  <Text style={styles.sectionTitle}>Service area and expertise</Text>
                  <View style={styles.fieldGrid}>
                    <FormField label="State" value={fields.state} onChangeText={(value) => updateField("state", value)} placeholder="State" autoCapitalize="words" />
                    <FormField label="Local government" value={fields.local_government} onChangeText={(value) => updateField("local_government", value)} placeholder="Local government area" autoCapitalize="words" />
                    <FormField label="Union name (optional)" value={fields.union_name} onChangeText={(value) => updateField("union_name", value)} placeholder="Union or association" autoCapitalize="words" />
                    <FormField label="Union location (optional)" value={fields.union_location} onChangeText={(value) => updateField("union_location", value)} placeholder="Union location" autoCapitalize="words" />
                  </View>
                  <Text style={styles.label}>Services offered</Text>
                  <View style={styles.serviceChoices}>
                    {mechanicServices.map((service) => {
                      const selected = services.includes(service);
                      return (
                        <Pressable
                          key={service}
                          accessibilityRole="checkbox"
                          accessibilityState={{ checked: selected }}
                          aria-checked={selected}
                          onPress={() => toggleService(service)}
                          style={[styles.serviceChoice, selected && styles.serviceChoiceSelected]}
                        >
                          <Text style={[styles.serviceChoiceText, selected && styles.serviceChoiceTextSelected]}>{service}</Text>
                        </Pressable>
                      );
                    })}
                  </View>
                  <FormField label="Vehicle model (optional)" value={fields.vehicle_model} onChangeText={(value) => updateField("vehicle_model", value)} placeholder="Example: Toyota Corolla" autoCapitalize="words" />
                  <FormField label="License number (optional)" value={fields.license_no} onChangeText={(value) => updateField("license_no", value)} placeholder="Driving or trade license" autoCapitalize="characters" />
                </View>
              ) : (
                <View style={styles.optionalFields}>
                  <Text style={styles.sectionTitle}>Vehicle details (optional)</Text>
                  <FormField label="Vehicle model" value={fields.vehicle_model} onChangeText={(value) => updateField("vehicle_model", value)} placeholder="Example: Toyota Corolla" autoCapitalize="words" />
                  <FormField label="License number" value={fields.license_no} onChangeText={(value) => updateField("license_no", value)} placeholder="Driving license number" autoCapitalize="characters" />
                </View>
              )}

              {fields.password_confirm && fields.password !== fields.password_confirm ? (
                <Text accessibilityRole="alert" style={styles.error}>Passwords do not match.</Text>
              ) : null}
              {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}

              <PrimaryButton
                label="Create account"
                loading={submitting}
                disabled={!formIsValid || Boolean(configurationIssue)}
                onPress={() => void handleRegister()}
                style={styles.submitButton}
              />
              <Pressable accessibilityRole="button" onPress={() => router.replace("/sign-in")} style={styles.textLinkButton}>
                <Text style={styles.textLink}>Already have an account? Sign in</Text>
              </Pressable>
            </View>
          )}
        </View>
      </KeyboardAvoidingView>
    </ScreenFrame>
  );
}

interface FormFieldProps {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  placeholder: string;
  autoCapitalize?: TextInputProps["autoCapitalize"];
  autoComplete?: TextInputProps["autoComplete"];
  keyboardType?: TextInputProps["keyboardType"];
  secureTextEntry?: boolean;
}

function FormField({ label, value, onChangeText, placeholder, ...inputProps }: FormFieldProps) {
  return (
    <View style={styles.fieldGroup}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        autoCorrect={false}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={colors.muted}
        style={styles.input}
        value={value}
        {...inputProps}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screenContent: {
    justifyContent: "center",
    paddingVertical: 20,
  },
  card: {
    gap: 22,
    padding: 24,
    borderRadius: 26,
    backgroundColor: colors.paper,
    borderWidth: 1,
    borderColor: colors.line,
  },
  brandRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  brandName: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "700",
  },
  brandCaption: {
    marginTop: 3,
    color: colors.muted,
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 1.25,
  },
  formContent: {
    gap: 16,
  },
  successContent: {
    gap: 16,
  },
  eyebrow: {
    color: colors.teal,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1.2,
  },
  title: {
    color: colors.ink,
    fontSize: 27,
    lineHeight: 33,
    fontWeight: "700",
  },
  body: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 21,
  },
  emailAddress: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "700",
  },
  roleChoices: {
    flexDirection: "row",
    gap: 10,
  },
  roleChoice: {
    minHeight: 44,
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.white,
  },
  roleChoiceSelected: {
    borderColor: colors.teal,
    backgroundColor: colors.tealSoft,
  },
  roleChoiceText: {
    color: colors.muted,
    fontSize: 14,
    fontWeight: "600",
  },
  roleChoiceTextSelected: {
    color: colors.teal,
    fontWeight: "700",
  },
  configurationNotice: {
    gap: 5,
    padding: 14,
    borderRadius: 15,
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
  fieldGrid: {
    gap: 13,
  },
  fieldGroup: {
    gap: 7,
  },
  label: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: "700",
  },
  input: {
    minHeight: 50,
    paddingHorizontal: 14,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.white,
    color: colors.ink,
    fontSize: 15,
  },
  mechanicFields: {
    gap: 14,
  },
  optionalFields: {
    gap: 14,
  },
  sectionTitle: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: "700",
  },
  serviceChoices: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  serviceChoice: {
    minHeight: 38,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 12,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.white,
  },
  serviceChoiceSelected: {
    borderColor: colors.teal,
    backgroundColor: colors.tealSoft,
  },
  serviceChoiceText: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "600",
  },
  serviceChoiceTextSelected: {
    color: colors.teal,
    fontWeight: "700",
  },
  error: {
    color: colors.red,
    fontSize: 13,
    lineHeight: 19,
  },
  successNotice: {
    color: colors.teal,
    fontSize: 13,
    lineHeight: 19,
  },
  submitButton: {
    marginTop: 2,
  },
  textLinkButton: {
    minHeight: 40,
    alignItems: "center",
    justifyContent: "center",
  },
  textLink: {
    color: colors.teal,
    fontSize: 13,
    fontWeight: "700",
  },
});
