"use client";

import { useCallback, useEffect, useState } from "react";
import * as notifApi from "@/lib/api/notifications";
import type { Device, UpdateDevicePreferencesPayload } from "@/types/notification";

const DEVICE_ID_KEY = "merygoround_device_id";

function getStoredDeviceId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(DEVICE_ID_KEY);
}

function setStoredDeviceId(id: string | null): void {
  if (typeof window === "undefined") return;
  if (id === null) localStorage.removeItem(DEVICE_ID_KEY);
  else localStorage.setItem(DEVICE_ID_KEY, id);
}

function urlBase64ToArrayBuffer(base64String: string): ArrayBuffer {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64);
  const buffer = new ArrayBuffer(raw.length);
  const view = new Uint8Array(buffer);
  for (let i = 0; i < raw.length; i++) view[i] = raw.charCodeAt(i);
  return buffer;
}

function defaultDeviceLabel(): string {
  if (typeof navigator === "undefined") return "Browser";
  const ua = navigator.userAgent;
  if (/iPhone|iPad|iPod/.test(ua)) return "iPhone/iPad";
  if (/Android/.test(ua)) return "Android";
  if (/Macintosh/.test(ua)) return "Mac";
  if (/Windows/.test(ua)) return "Windows";
  if (/Linux/.test(ua)) return "Linux";
  return "Browser";
}

/**
 * Manage push notification subscriptions and preferences for the CURRENT device.
 *
 * The device is identified by a UUID stored in localStorage; preferences live
 * server-side keyed by that UUID. Other devices are not affected by toggles
 * performed here.
 */
export function useNotifications() {
  const [device, setDevice] = useState<Device | null>(null);
  const [otherDevices, setOtherDevices] = useState<Device[]>([]);
  const [permission, setPermission] = useState<NotificationPermission>("default");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (typeof window !== "undefined" && "Notification" in window) {
      setPermission(Notification.permission);
    }
  }, []);

  const refreshDevices = useCallback(async () => {
    try {
      const all = await notifApi.listDevices();
      const id = getStoredDeviceId();
      const current = id ? all.find((d) => d.id === id) ?? null : null;
      if (!current && id) {
        setStoredDeviceId(null);
      }
      setDevice(current);
      setOtherDevices(all.filter((d) => d.id !== current?.id));
    } catch {
      /* not authenticated yet, ignore */
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    refreshDevices().finally(() => {
      if (!cancelled) setIsLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [refreshDevices]);

  const requestPermission = useCallback(async (): Promise<NotificationPermission> => {
    if (typeof window === "undefined" || !("Notification" in window)) {
      return "denied";
    }
    const result = await Notification.requestPermission();
    setPermission(result);
    return result;
  }, []);

  const enable = useCallback(async (): Promise<Device | null> => {
    if (!("serviceWorker" in navigator)) {
      console.warn("[merygoround] service worker unsupported");
      return null;
    }

    const perm = await requestPermission();
    if (perm !== "granted") {
      console.warn("[merygoround] notification permission not granted:", perm);
      return null;
    }

    const registration = await navigator.serviceWorker.ready;
    const vapidKey = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY;
    if (!vapidKey) {
      throw new Error("NEXT_PUBLIC_VAPID_PUBLIC_KEY is not set");
    }

    const existing = await registration.pushManager.getSubscription();
    if (existing) {
      console.info("[merygoround] dropping stale browser subscription before re-subscribing");
      try {
        await existing.unsubscribe();
      } catch (err) {
        console.warn("[merygoround] failed to unsubscribe stale subscription", err);
      }
    }

    const browserSub = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToArrayBuffer(vapidKey),
    });
    const json = browserSub.toJSON();
    console.info("[merygoround] new push subscription", {
      endpoint: json.endpoint?.slice(0, 60) + "...",
    });

    const newDevice = await notifApi.subscribe({
      endpoint: json.endpoint!,
      p256dh_key: json.keys!.p256dh!,
      auth_key: json.keys!.auth!,
      device_label: defaultDeviceLabel(),
    });

    setStoredDeviceId(newDevice.id);
    setDevice(newDevice);
    await refreshDevices();
    return newDevice;
  }, [requestPermission, refreshDevices]);

  const disable = useCallback(async (): Promise<void> => {
    const id = getStoredDeviceId();
    if ("serviceWorker" in navigator) {
      try {
        const registration = await navigator.serviceWorker.ready;
        const browserSub = await registration.pushManager.getSubscription();
        if (browserSub) {
          await browserSub.unsubscribe();
        }
      } catch {
        /* best effort; backend deletion is the source of truth */
      }
    }
    if (id) {
      try {
        await notifApi.unsubscribeDevice(id);
      } catch {
        /* device may already be gone server-side */
      }
    }
    setStoredDeviceId(null);
    setDevice(null);
    await refreshDevices();
  }, [refreshDevices]);

  const updatePreferences = useCallback(
    async (payload: UpdateDevicePreferencesPayload) => {
      if (!device) return null;
      const updated = await notifApi.updateDevice(device.id, payload);
      setDevice(updated);
      return updated;
    },
    [device],
  );

  const sendTest = useCallback(async () => {
    if (!device) return;
    await notifApi.sendTestPush(device.id);
  }, [device]);

  const removeOtherDevice = useCallback(
    async (id: string) => {
      await notifApi.unsubscribeDevice(id);
      await refreshDevices();
    },
    [refreshDevices],
  );

  return {
    device,
    otherDevices,
    permission,
    isLoading,
    requestPermission,
    enable,
    disable,
    updatePreferences,
    sendTest,
    removeOtherDevice,
    refreshDevices,
  };
}
