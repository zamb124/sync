export type WsConnectionState = "connecting" | "open" | "closed";

export type ReliableWsOptions = {
  token: string;
  onMessage: (data: string) => void;
  onOpen?: () => void;
  onClose?: (e: CloseEvent) => void;
  onError?: () => void;
};

export type ReliableWs = {
  getState: () => WsConnectionState;
  sendJson: (payload: unknown) => void;
  close: () => void;
};

function buildWsUrl(token: string): string {
  if (token.trim() === "") {
    throw new Error("token обязателен для WebSocket.");
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const url = new URL("/ws", window.location.href);
  url.protocol = protocol;
  url.searchParams.set("token", token);
  return url.toString();
}

function jitter(ms: number): number {
  const spread = 0.2;
  const delta = ms * spread;
  return Math.max(0, Math.round(ms - delta + Math.random() * (2 * delta)));
}

export function createReliableWs(opts: ReliableWsOptions): ReliableWs {
  let state: WsConnectionState = "closed";
  let socket: WebSocket | null = null;
  let stopped = false;
  let reconnectTimer: number | null = null;
  let attempt = 0;

  const baseDelayMs = 600;
  const maxDelayMs = 60_000;

  const cleanupTimer = (): void => {
    if (reconnectTimer !== null) {
      window.clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  };

  const scheduleReconnect = (reason: string): void => {
    if (stopped) {
      return;
    }
    cleanupTimer();
    attempt += 1;
    const exp = Math.min(maxDelayMs, Math.round(baseDelayMs * Math.pow(1.7, attempt)));
    const delay = jitter(exp);
    state = "connecting";
    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = null;
      connect(`timer:${reason}`);
    }, delay);
  };

  const connect = (_reason: string): void => {
    if (stopped) {
      return;
    }
    if (socket !== null) {
      return;
    }
    state = "connecting";
    const url = buildWsUrl(opts.token);
    const ws = new WebSocket(url);
    socket = ws;

    ws.onopen = () => {
      if (socket !== ws) {
        return;
      }
      attempt = 0;
      state = "open";
      opts.onOpen?.();
    };

    ws.onmessage = (e) => {
      if (socket !== ws) {
        return;
      }
      if (typeof e.data !== "string") {
        return;
      }
      opts.onMessage(e.data);
    };

    ws.onerror = () => {
      if (socket !== ws) {
        return;
      }
      opts.onError?.();
    };

    ws.onclose = (e) => {
      if (socket !== ws) {
        return;
      }
      socket = null;
      state = "closed";
      opts.onClose?.(e);
      scheduleReconnect(`close:${e.code}`);
    };
  };

  const onOnline = (): void => {
    if (stopped) {
      return;
    }
    if (socket !== null) {
      return;
    }
    attempt = Math.max(0, attempt - 1);
    cleanupTimer();
    connect("online");
  };

  const onVisibility = (): void => {
    if (stopped) {
      return;
    }
    if (document.visibilityState !== "visible") {
      return;
    }
    if (socket !== null) {
      return;
    }
    attempt = Math.max(0, attempt - 1);
    cleanupTimer();
    connect("visible");
  };

  window.addEventListener("online", onOnline);
  document.addEventListener("visibilitychange", onVisibility);

  connect("init");

  return {
    getState: () => state,
    sendJson: (payload: unknown) => {
      const ws = socket;
      if (ws === null || ws.readyState !== WebSocket.OPEN) {
        throw new Error("WebSocket не подключен.");
      }
      ws.send(JSON.stringify(payload));
    },
    close: () => {
      stopped = true;
      cleanupTimer();
      window.removeEventListener("online", onOnline);
      document.removeEventListener("visibilitychange", onVisibility);
      const ws = socket;
      socket = null;
      state = "closed";
      try {
        ws?.close();
      } catch {
        // ignore
      }
    },
  };
}

