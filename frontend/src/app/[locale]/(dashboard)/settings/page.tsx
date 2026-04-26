"use client";

import { useCallback, useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import { useRouter, usePathname } from "@/i18n/navigation";
import { useNotifications } from "@/lib/hooks/use-notifications";
import { BucketSettingsCard } from "@/components/bucket/bucket-settings-card";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Bell, BellOff, Globe, Clock, Moon } from "lucide-react";
import { toast } from "sonner";
import type { Locale } from "@/i18n/routing";

/** Settings page for notifications, language, and quiet hours. */
export default function SettingsPage() {
  const t = useTranslations("settings");
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const {
    preferences,
    permission,
    requestPermission,
    subscribeToPush,
    unsubscribeFromPush,
    updatePreferences,
  } = useNotifications();

  const [isSaving, setIsSaving] = useState(false);

  const handleToggleNotifications = useCallback(async () => {
    setIsSaving(true);
    try {
      if (preferences?.enabled) {
        await unsubscribeFromPush();
        await updatePreferences({ enabled: false });
        toast.success(t("saved"));
      } else {
        const perm = await requestPermission();
        if (perm === "denied") {
          toast.error(t("notificationPermissionDenied"));
          return;
        }
        await subscribeToPush();
        await updatePreferences({ enabled: true });
        toast.success(t("saved"));
      }
    } catch {
      toast.error(t("saved"));
    } finally {
      setIsSaving(false);
    }
  }, [preferences, requestPermission, subscribeToPush, unsubscribeFromPush, updatePreferences, t]);

  const handleIntervalChange = useCallback(
    async (value: string | null) => {
      if (!value) return;
      setIsSaving(true);
      try {
        await updatePreferences({ interval_minutes: parseInt(value) });
        toast.success(t("saved"));
      } catch {
        toast.error(t("saved"));
      } finally {
        setIsSaving(false);
      }
    },
    [updatePreferences, t],
  );

  const handleQuietHoursChange = useCallback(
    async (field: "quiet_hours_start" | "quiet_hours_end", value: string | null) => {
      if (!value) return;
      setIsSaving(true);
      try {
        await updatePreferences({ [field]: parseInt(value) });
        toast.success(t("saved"));
      } catch {
        toast.error(t("saved"));
      } finally {
        setIsSaving(false);
      }
    },
    [updatePreferences, t],
  );

  function switchLocale(newLocale: Locale) {
    router.replace(pathname, { locale: newLocale });
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold text-foreground">{t("title")}</h1>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900">
              {preferences?.enabled ? (
                <Bell className="size-5 text-indigo-600 dark:text-indigo-400" />
              ) : (
                <BellOff className="size-5 text-muted-foreground" />
              )}
            </div>
            <div>
              <CardTitle className="text-base">{t("notifications")}</CardTitle>
              <CardDescription>{t("notificationsDescription")}</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label>{preferences?.enabled ? t("enabled") : t("disabled")}</Label>
            <Button
              variant={preferences?.enabled ? "outline" : "default"}
              size="sm"
              onClick={handleToggleNotifications}
              disabled={isSaving || permission === "denied"}
              className={
                !preferences?.enabled
                  ? "bg-indigo-600 hover:bg-indigo-700 text-white"
                  : ""
              }
            >
              {preferences?.enabled ? t("disable") : t("enable")}
            </Button>
          </div>

          {preferences?.enabled && (
            <>
              <Separator />

              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Clock className="size-4 text-muted-foreground" />
                  <Label>{t("interval")}</Label>
                </div>
                <Select
                  value={String(preferences.interval_minutes || 60)}
                  onValueChange={handleIntervalChange}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="30">{t("intervalOptions.30")}</SelectItem>
                    <SelectItem value="60">{t("intervalOptions.60")}</SelectItem>
                    <SelectItem value="120">{t("intervalOptions.120")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Moon className="size-4 text-muted-foreground" />
                  <div>
                    <Label>{t("quietHours")}</Label>
                    <p className="text-xs text-muted-foreground">{t("quietHoursDescription")}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs">{t("quietStart")}</Label>
                    <Select
                      value={String(preferences.quiet_hours_start ?? 22)}
                      onValueChange={(v) => handleQuietHoursChange("quiet_hours_start", v)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {Array.from({ length: 24 }, (_, i) => (
                          <SelectItem key={i} value={String(i)}>
                            {i.toString().padStart(2, "0")}:00
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">{t("quietEnd")}</Label>
                    <Select
                      value={String(preferences.quiet_hours_end ?? 8)}
                      onValueChange={(v) => handleQuietHoursChange("quiet_hours_end", v)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {Array.from({ length: 24 }, (_, i) => (
                          <SelectItem key={i} value={String(i)}>
                            {i.toString().padStart(2, "0")}:00
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <BucketSettingsCard kind="adult" titleNamespace="bucket" />
      <BucketSettingsCard kind="happy" titleNamespace="happyBucket" />

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
              <Globe className="size-5 text-purple-600 dark:text-purple-400" />
            </div>
            <CardTitle className="text-base">{t("language")}</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <Button
              variant={locale === "en" ? "default" : "outline"}
              className={locale === "en" ? "bg-indigo-600 hover:bg-indigo-700 text-white" : ""}
              onClick={() => switchLocale("en")}
            >
              English
            </Button>
            <Button
              variant={locale === "pt-BR" ? "default" : "outline"}
              className={locale === "pt-BR" ? "bg-indigo-600 hover:bg-indigo-700 text-white" : ""}
              onClick={() => switchLocale("pt-BR")}
            >
              Portugues (BR)
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
