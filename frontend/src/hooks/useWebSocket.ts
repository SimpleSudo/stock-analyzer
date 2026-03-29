import { useEffect, useRef, useState, useCallback } from 'react';

interface UseWebSocketOptions {
  onMessage?: (data: any) => void;
  reconnectInterval?: number;
  maxRetries?: number;
}

export const useWebSocket = (url: string | null, options: UseWebSocketOptions = {}) => {
  const { onMessage, reconnectInterval = 5000, maxRetries = 10 } = options;
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const urlRef = useRef(url);

  urlRef.current = url;

  const connect = useCallback(() => {
    if (!urlRef.current) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}${urlRef.current}`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setConnected(true);
        retriesRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          onMessage?.(data);
        } catch {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;
        if (retriesRef.current < maxRetries && urlRef.current) {
          retriesRef.current++;
          setTimeout(connect, reconnectInterval);
        }
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRef.current = ws;
    } catch {
      // connection failed
    }
  }, [onMessage, reconnectInterval, maxRetries]);

  useEffect(() => {
    if (url) {
      connect();
    }
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [url, connect]);

  const disconnect = useCallback(() => {
    retriesRef.current = maxRetries; // prevent reconnect
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, [maxRetries]);

  return { connected, lastMessage, disconnect };
};
