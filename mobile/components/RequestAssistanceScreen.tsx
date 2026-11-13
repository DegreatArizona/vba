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

import { PrimaryButton } from "./PrimaryButton";
import { ScreenFrame } from "./ScreenFrame";
import { ApiError, createRequest, getApiConfigurationIssue } from "../lib/api";
import { colors } from "../lib/theme";
import { useAuth } from "../lib/auth";
import type { RequestCreateInput, ServiceCategory } from "../lib/types";

const categories: ServiceCategory[] = [
  "Tire Repair",
  "Towing Service",
  "Battery Jumpstart",
  "Electrical Issues",
  "Engine Repair",
  "Bodywork/Collision Repair",
  "Other Service",
];

interface RequestFormValues extends Omit<RequestCreateInput, "category"> {
  category: ServiceCategory | "";
}

const initialForm: RequestFormValues = {
  category: "",
  vehicle_no: "",
  vehicle_name: "",
  problem_description: "",
  state: "",
  location: "",
  mobile: "",
};

export function RequestAssistanceScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const [form, setForm] = useState<RequestFormValues>(initialForm);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const configurationIssue = getApiConfigurationIssue();

  if (!user) return null;

  if (user.role !== "driver") {
    return (
      <ScreenFrame contentStyle={styles.content}>
        <StateNotice
          title="Driver requests only"
          body="This request form is available to verified driver accounts."
        />
      </ScreenFrame>
    );
  }

  if (!user.is_email_verified) {
    return (
      <ScreenFrame contentStyle={styles.content}>
        <StateNotice
          title="Verify your email first"
          body="Your account must be verified before you can send a roadside service request."
        />
      </ScreenFrame>
    );
  }

  function updateField<Field extends keyof RequestFormValues>(field: Field, value: RequestFormValues[Field]) {
    setForm((current) => ({ ...current, [field]: value }));
    setSubmitError(null);
  }

  async function handleSubmit() {
    if (submitting || configurationIssue) return;

    const requiredValues = [
      form.vehicle_no,
      form.vehicle_name,
      form.problem_description,
      form.state,
      form.location,
      form.mobile,
    ];
    if (!form.category || requiredValues.some((value) => !value.trim())) {
      setSubmitError("Complete every required field before sending your request.");
      return;
    }

    setSubmitError(null);
    setSubmitting(true);
    try {
      const payload: RequestCreateInput = {
        ...form,
        category: form.category,
        vehicle_no: form.vehicle_no.trim(),
        vehicle_name: form.vehicle_name.trim(),
        problem_description: form.problem_description.trim(),
        state: form.state.trim(),
        location: form.location.trim(),
        mobile: form.mobile.trim(),
      };
      const created = await createRequest(payload);
      router.replace({
        pathname: "/(app)/request-details",
        params: { requestId: String(created.id) },
      });
    } catch (caught) {
      setSubmitError(
        caught instanceof ApiError
          ? caught.message
          : "The service request could not be sent. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <ScreenFrame contentStyle={styles.content}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <View style={styles.container}>
          <Pressable
            accessibilityRole="button"
            onPress={() => (router.canGoBack() ? router.back() : router.replace("/(app)"))}
            style={styles.backButton}
          >
            <Text style={styles.backLabel}>Back to activity</Text>
          </Pressable>

          <View style={styles.heading}>
            <Text style={styles.eyebrow}>DRIVER SERVICE REQUEST</Text>
            <Text style={styles.title}>Tell us what happened.</Text>
            <Text style={styles.description}>
              Share your vehicle, issue, and exact location. Auto Aid will review the request before a mechanic is assigned.
            </Text>
          </View>

          {configurationIssue ? (
            <StateNotice title="Connect the service API" body={configurationIssue} />
          ) : null}

          <View style={styles.formCard}>
            <Text style={styles.sectionTitle}>What service do you need?</Text>
            <CategoryPicker value={form.category} onChange={(value) => updateField("category", value)} />

            <View style={styles.twoColumnRow}>
              <FormField
                autoCapitalize="characters"
                label="Plate number *"
                maxLength={150}
                onChangeText={(value) => updateField("vehicle_no", value)}
                placeholder="ABC-123"
                value={form.vehicle_no}
              />
              <FormField
                label="Vehicle *"
                maxLength={140}
                onChangeText={(value) => updateField("vehicle_name", value)}
                placeholder="Make and model"
                value={form.vehicle_name}
              />
            </View>

            <FormField
              label="State *"
              maxLength={255}
              onChangeText={(value) => updateField("state", value)}
              placeholder="State"
              value={form.state}
            />
            <FormField
              label="Current location *"
              maxLength={255}
              onChangeText={(value) => updateField("location", value)}
              placeholder="Street, area, and nearby landmark"
              value={form.location}
            />
            <FormField
              keyboardType="phone-pad"
              label="Contact phone *"
              maxLength={40}
              onChangeText={(value) => updateField("mobile", value)}
              placeholder="Phone number we can reach"
              value={form.mobile}
            />
            <FormField
              label="Describe the problem *"
              maxLength={500}
              multiline
              onChangeText={(value) => updateField("problem_description", value)}
              placeholder="What happened, and what help do you need?"
              value={form.problem_description}
            />

            <View style={styles.paymentNote}>
              <Text style={styles.paymentTitle}>No payment is collected here</Text>
              <Text style={styles.paymentCopy}>
                A manager reviews the request and confirms service details before any payment step.
              </Text>
            </View>

            {submitError ? (
              <Text accessibilityRole="alert" accessibilityLiveRegion="polite" style={styles.errorText}>
                {submitError}
              </Text>
            ) : null}

            <PrimaryButton
              disabled={Boolean(configurationIssue)}
              label="Send service request"
              loading={submitting}
              onPress={() => void handleSubmit()}
            />
          </View>
        </View>
      </KeyboardAvoidingView>
    </ScreenFrame>
  );
}

function FormField({
  label,
  value,
  onChangeText,
  placeholder,
  maxLength,
  multiline = false,
  keyboardType = "default",
  autoCapitalize = "sentences",
}: {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  placeholder: string;
  maxLength: number;
  multiline?: boolean;
  keyboardType?: TextInputProps["keyboardType"];
  autoCapitalize?: TextInputProps["autoCapitalize"];
}) {
  return (
    <View style={styles.fieldGroup}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        autoCapitalize={autoCapitalize}
        autoCorrect={false}
        keyboardType={keyboardType}
        maxLength={maxLength}
        multiline={multiline}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={colors.muted}
        style={[styles.input, multiline && styles.multilineInput]}
        textAlignVertical={multiline ? "top" : "center"}
        value={value}
      />
    </View>
  );
}

function CategoryPicker({
  value,
  onChange,
}: {
  value: ServiceCategory | "";
  onChange: (value: ServiceCategory) => void;
}) {
  return (
    <View accessibilityLabel="Service category" accessibilityRole="radiogroup" style={styles.categoryList}>
      {categories.map((category) => {
        const selected = value === category;
        return (
          <Pressable
            key={category}
            accessibilityLabel={category}
            accessibilityRole="radio"
            accessibilityState={{ checked: selected }}
            onPress={() => onChange(category)}
            style={[styles.categoryOption, selected && styles.categorySelected]}
          >
            <Text style={[styles.categoryText, selected && styles.categorySelectedText]}>{category}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

function StateNotice({ title, body }: { title: string; body: string }) {
  return (
    <View accessibilityRole="alert" style={styles.notice}>
      <Text style={styles.noticeTitle}>{title}</Text>
      <Text style={styles.noticeBody}>{body}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  content: {
    paddingHorizontal: 20,
    paddingTop: 14,
    paddingBottom: 32,
  },
  container: {
    width: "100%",
    maxWidth: 660,
    alignSelf: "center",
    gap: 20,
  },
  backButton: {
    minHeight: 44,
    alignSelf: "flex-start",
    justifyContent: "center",
    paddingHorizontal: 4,
  },
  backLabel: {
    color: colors.teal,
    fontSize: 14,
    fontWeight: "700",
  },
  heading: {
    gap: 8,
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
  description: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 21,
  },
  formCard: {
    gap: 18,
    padding: 20,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: 22,
    backgroundColor: colors.paper,
  },
  sectionTitle: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "700",
  },
  categoryList: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 9,
  },
  categoryOption: {
    minHeight: 42,
    justifyContent: "center",
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: 999,
    paddingHorizontal: 13,
    backgroundColor: colors.white,
  },
  categorySelected: {
    borderColor: colors.teal,
    backgroundColor: colors.tealSoft,
  },
  categoryText: {
    color: colors.inkSoft,
    fontSize: 12,
    fontWeight: "600",
  },
  categorySelectedText: {
    color: colors.teal,
    fontWeight: "700",
  },
  twoColumnRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
  },
  fieldGroup: {
    flexGrow: 1,
    flexBasis: 230,
    gap: 7,
  },
  fieldLabel: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: "700",
  },
  input: {
    minHeight: 50,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: 14,
    paddingHorizontal: 14,
    color: colors.ink,
    backgroundColor: colors.white,
    fontSize: 14,
  },
  multilineInput: {
    minHeight: 112,
    paddingTop: 13,
  },
  paymentNote: {
    gap: 5,
    borderRadius: 15,
    padding: 14,
    backgroundColor: colors.tealSoft,
  },
  paymentTitle: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: "700",
  },
  paymentCopy: {
    color: colors.inkSoft,
    fontSize: 12,
    lineHeight: 18,
  },
  errorText: {
    color: colors.red,
    fontSize: 13,
    lineHeight: 19,
  },
  notice: {
    gap: 5,
    borderRadius: 16,
    padding: 16,
    backgroundColor: colors.amberSoft,
    borderWidth: 1,
    borderColor: "#EBD09E",
  },
  noticeTitle: {
    color: colors.ink,
    fontSize: 14,
    fontWeight: "700",
  },
  noticeBody: {
    color: colors.inkSoft,
    fontSize: 13,
    lineHeight: 19,
  },
});
