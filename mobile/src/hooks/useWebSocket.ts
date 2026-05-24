import { useEffect, useRef, useCallback } from "react";
import config from "../services/config";
import { getAccessToken } from "../services/api";

type PriceUpdate = Record<string, { price: number; change_pct: number }>;
type Callback = (data: PriceUpdate) => void;

export function useWebSocket(symbols: string[], onUpdate: Callback) {
  const wsRef = useRef<WebSocket | null>(null);
  const onUpdateRef = useRef(onUpdate);
  onUpdateRef.current = onUpdate;

  const connect = useCallback(() => {
    const token = getAccessToken();
    if (!token || symbols.length === 0) return;

    const ws = new WebSocket(`${config.wsBaseUrl}/prices?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ action: "subscribe", symbols }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as PriceUpdate;
        onUpdateRef.current(data);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onerror = () => {
      // Will auto-reconnect via onclose
    };

    ws.onclose = () => {
      wsRef.current = null;
      // Reconnect after 5 seconds
      setTimeout(connect, 5000);
    };
  }, [symbols.join(",")]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [connect]);
}
