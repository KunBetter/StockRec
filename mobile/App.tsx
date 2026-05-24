import React from "react";
import { StatusBar } from "react-native";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { AuthProvider, useAuth } from "./src/store/AuthContext";

import RecommendationsScreen from "./src/screens/RecommendationsScreen";
import MarketScreen from "./src/screens/MarketScreen";
import ProfileScreen from "./src/screens/ProfileScreen";
import LoginScreen from "./src/screens/LoginScreen";
import StockDetailScreen from "./src/screens/StockDetailScreen";

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: "#34d399",
        tabBarInactiveTintColor: "#666",
        tabBarStyle: {
          backgroundColor: "#111",
          borderTopColor: "#222",
        },
      }}
    >
      <Tab.Screen
        name="Recommendations"
        component={RecommendationsScreen}
        options={{ tabBarLabel: "推荐" }}
      />
      <Tab.Screen
        name="Market"
        component={MarketScreen}
        options={{ tabBarLabel: "行情" }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{ tabBarLabel: "我的" }}
      />
    </Tab.Navigator>
  );
}

function RootNavigator() {
  const { isSignedIn } = useAuth();

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {isSignedIn ? (
        <>
          <Stack.Screen name="Main" component={MainTabs} />
          <Stack.Screen
            name="StockDetail"
            component={StockDetailScreen}
            options={{ animation: "slide_from_right" }}
          />
        </>
      ) : (
        <Stack.Screen name="Login" component={LoginScreen} />
      )}
    </Stack.Navigator>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <StatusBar barStyle="light-content" backgroundColor="#000" />
      <AuthProvider>
        <NavigationContainer>
          <RootNavigator />
        </NavigationContainer>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
