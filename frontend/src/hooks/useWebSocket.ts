import { useEffect, useRef, useState, useCallback } from 'react';

interface UseWebSocketOptions {
  onMessage?: (data: any) => void;
  maxRetries?: number;
  heartbeatTimeout?: number;
}

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

/**
 * WebSocket Hook — 指数退避重连 + 心跳检测
 * - 收到 {"type":"ping"} 回复 {"type":"pong"}
 * - heartbeatTimeout 毫秒内无消息则主动重连
 * - 重连间隔: 1s → 2s → 4s → ... → max 30s
 */
export const useWebSocket = (url: string | null, options: UseWebSocketOptions = {}) => {
  const { onMessage, maxRetries = 20, heartbeatTimeout = 30000 } = options;
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const urlRef = useRef(url);
  const heartbeatTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const unmountedRef = useRef(false);

  urlRef.current = url;

  const clearTimers = useCallback(() => {
    if (heartbeatTimerRef.current) {
      clearTimeout(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  }, []);

  const resetHeartbeat = useCallback(() => {
    if (heartbeatTimerRef.current) clearTimeout(heartbeatTimerRef.current);
    heartbeatTimerRef.current = setTimeout(() => {
      // 心跳超时，主动关闭触发重连
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    }, heartbeatTimeout);
  }, [heartbeatTimeout]);

  const connect = useCallback(() => {
    if (!urlRef.current || unmountedRef.current) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}${urlRef.current}`;

    setStatus('connecting');
    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        if (unmountedRef.current) { ws.close(); return; }
        setStatus('connected');
        retriesRef.current = 0;
        resetHeartbeat();
      };

      ws.onmessage = (event) => {
        resetHeartbeat();
        try {
          const data = JSON.parse(event.data);
          // 心跳 ping → 回复 pong
          if (data?.type === 'ping') {
            ws.send(JSON.stringify({ type: 'pong' }));
            return;
          }
          setLastMessage(data);
          onMessage?.(data);
        } catch {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        if (unmountedRef.current) return;
        setStatus('disconnected');
        wsRef.current = null;
        clearTimers();

        if (retriesRef.current < maxRetries && urlRef.current) {
          // 指数退避: 1s, 2s, 4s, 8s, ... max 30s
          const delay = Math.min(1000 * Math.pow(2, retriesRef.current), 30000);
          retriesRef.current++;
          setStatus('reconnecting');
          reconnectTimerRef.current = setTimeout(connect, delay);
        }
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRef.current = ws;
    } catch {
      // connection failed
    }
  }, [onMessage, maxRetries, resetHeartbeat, clearTimers]);

  useEffect(() => {
    unmountedRef.current = false;
    if (url) {
      retriesRef.current = 0;
      connect();
    }
    return () => {
      unmountedRef.current = true;
      clearTimers();
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [url]);  // eslint-disable-line react-hooks/exhaustive-deps

  const disconnect = useCallback(() => {
    retriesRef.current = maxRetries;
    clearTimers();
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, [maxRetries, clearTimers]);

  // backward compatibility: expose `connected` boolean
  const connected = status === 'connected';

  return { connected, status, lastMessage, disconnect };
};
