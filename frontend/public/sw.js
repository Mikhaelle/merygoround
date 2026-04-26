self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (err) {
    console.error("[sw] failed to parse push payload", err);
  }
  const title = data.title || "MeryGoRound";
  const options = {
    body: data.body || "Time to spin the wheel!",
    icon: data.icon || "/icons/icon-192.png",
    badge: data.badge || "/icons/icon-192.png",
    data: { url: data.url || "/" },
    requireInteraction: false,
  };
  event.waitUntil(
    self.registration
      .showNotification(title, options)
      .catch((err) => console.error("[sw] showNotification failed", err)),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data?.url || "/";
  event.waitUntil(
    self.clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((clients) => {
        for (const client of clients) {
          if ("focus" in client) {
            client.focus();
            if ("navigate" in client) client.navigate(url).catch(() => {});
            return;
          }
        }
        return self.clients.openWindow(url);
      }),
  );
});
