import { Redirect, Tabs } from "expo-router";
import { SymbolView } from "expo-symbols";

import { LoadingScreen } from "@/components/LoadingScreen";
import { useAuth } from "@/lib/auth";
import { colors } from "@/lib/theme";

export default function AppTabsLayout() {
  const { user, isLoading, sessionError } = useAuth();

  if (isLoading) return <LoadingScreen />;
  if (!user || sessionError) return <Redirect href="/sign-in" />;

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        sceneStyle: { backgroundColor: colors.canvas },
        tabBarActiveTintColor: colors.teal,
        tabBarInactiveTintColor: colors.muted,
        tabBarStyle: {
          height: 64,
          paddingTop: 7,
          paddingBottom: 8,
          borderTopColor: colors.line,
          backgroundColor: colors.paper,
        },
        tabBarLabelStyle: { fontSize: 11, fontWeight: "600" },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Activity",
          tabBarAccessibilityLabel: "Service activity tab",
          tabBarIcon: ({ color }) => (
            <SymbolView
              name={{ ios: "list.bullet.rectangle", android: "list_alt", web: "view_list" }}
              tintColor={color}
              size={22}
            />
          ),
        }}
      />
      <Tabs.Screen
        name="queue"
        options={{
          title: "Queue",
          href: user.role === "manager" ? undefined : null,
          tabBarAccessibilityLabel: "State-scoped manager request queue",
          tabBarIcon: ({ color }) => (
            <SymbolView
              name={{ ios: "tray.full", android: "inbox", web: "inbox" }}
              tintColor={color}
              size={22}
            />
          ),
        }}
      />
      <Tabs.Screen
        name="team"
        options={{
          title: "Team",
          href: user.role === "manager" ? undefined : null,
          tabBarAccessibilityLabel: "Manager mechanic team",
          tabBarIcon: ({ color }) => (
            <SymbolView
              name={{ ios: "person.2", android: "group", web: "group" }}
              tintColor={color}
              size={22}
            />
          ),
        }}
      />
      <Tabs.Screen name="request-details" options={{ href: null }} />
      <Tabs.Screen name="request-assistance" options={{ href: null }} />
      <Tabs.Screen
        name="notifications"
        options={{
          title: "Inbox",
          tabBarAccessibilityLabel: "Notifications",
          tabBarIcon: ({ color }) => (
            <SymbolView
              name={{ ios: "bell", android: "notifications", web: "notifications" }}
              tintColor={color}
            />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: "Account",
          tabBarAccessibilityLabel: "Account profile tab",
          tabBarIcon: ({ color }) => (
            <SymbolView
              name={{ ios: "person.crop.circle", android: "account_circle", web: "account_circle" }}
              tintColor={color}
              size={22}
            />
          ),
        }}
      />
    </Tabs>
  );
}
