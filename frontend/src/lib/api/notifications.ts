import { apiClient } from "./client";
import type {
  Device,
  PushSubscriptionPayload,
  UpdateDevicePreferencesPayload,
} from "@/types/notification";

/** List every device subscribed for push for the current user. */
export async function listDevices(): Promise<Device[]> {
  const response = await apiClient.get<Device[]>("/notifications/devices");
  return response.data;
}

/** Register or refresh the current device's push subscription. */
export async function subscribe(payload: PushSubscriptionPayload): Promise<Device> {
  const response = await apiClient.post<Device>("/notifications/devices", payload);
  return response.data;
}

/** Get a single device's preferences. */
export async function getDevice(id: string): Promise<Device> {
  const response = await apiClient.get<Device>(`/notifications/devices/${id}`);
  return response.data;
}

/** Update a single device's preferences. */
export async function updateDevice(
  id: string,
  payload: UpdateDevicePreferencesPayload,
): Promise<Device> {
  const response = await apiClient.put<Device>(
    `/notifications/devices/${id}`,
    payload,
  );
  return response.data;
}

/** Remove a device's subscription. */
export async function unsubscribeDevice(id: string): Promise<void> {
  await apiClient.delete(`/notifications/devices/${id}`);
}

/** Send a one-off test push to verify the pipeline. */
export async function sendTestPush(id: string): Promise<void> {
  await apiClient.post(`/notifications/devices/${id}/test`);
}
