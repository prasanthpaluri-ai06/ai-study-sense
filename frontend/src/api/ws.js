/**
 * WebSocket helper connecting the frontend React application to the Laptop Backend
 * for real-time telemetry, ESP32 status updates, and posture feedback.
 */
export function createDashboardWebSocket(onMessage, onOpen, onClose) {
  const protocol = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = typeof window !== "undefined" && window.location.hostname ? window.location.hostname : "localhost";
  const wsUrl = `${protocol}//${host}:8000/ws/dashboard`;
  let socket = null;
  let isClosedManually = false;

  function connect() {
    socket = new WebSocket(wsUrl);

    socket.onopen = (event) => {
      console.log("[WS] Connected to AI StudySense Dashboard stream");
      if (onOpen) onOpen(event);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (onMessage) onMessage(data);
      } catch (err) {
        console.error("[WS] Error parsing message:", err);
      }
    };

    socket.onclose = (event) => {
      console.warn("[WS] Dashboard socket closed");
      if (onClose) onClose(event);
      if (!isClosedManually) {
        setTimeout(connect, 3000); // Auto reconnect
      }
    };

    socket.onerror = (err) => {
      console.error("[WS] Socket error:", err);
      socket.close();
    };
  }

  connect();

  return {
    send: (data) => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(typeof data === "string" ? data : JSON.stringify(data));
      }
    },
    close: () => {
      isClosedManually = true;
      if (socket) socket.close();
    },
  };
}
