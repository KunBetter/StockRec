import { Platform } from "react-native";

// Android emulator uses 10.0.2.2 to reach host machine
// iOS simulator uses localhost directly
const DEV_HOST = Platform.OS === "android" ? "10.0.2.2" : "localhost";

interface AppConfig {
  apiBaseUrl: string;
  wsBaseUrl: string;
}

const config: AppConfig = {
  apiBaseUrl: __DEV__
    ? `http://${DEV_HOST}:8000/api/v1`
    : "https://api.stockrec.example.com/api/v1",
  wsBaseUrl: __DEV__
    ? `ws://${DEV_HOST}:8000/ws`
    : "wss://api.stockrec.example.com/ws",
};

export default config;
