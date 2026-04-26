export interface PushSubscriptionPayload {
  endpoint: string;
  p256dh_key: string;
  auth_key: string;
  device_label?: string | null;
}

export interface Device {
  id: string;
  endpoint: string;
  enabled: boolean;
  interval_minutes: number;
  quiet_hours_start: number | null;
  quiet_hours_end: number | null;
  last_notified_at: string | null;
  device_label: string | null;
  created_at: string;
}

export interface UpdateDevicePreferencesPayload {
  enabled?: boolean;
  interval_minutes?: number;
  quiet_hours_start?: number;
  quiet_hours_end?: number;
  device_label?: string;
}
