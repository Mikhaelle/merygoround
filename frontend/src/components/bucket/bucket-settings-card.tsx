"use client";

import { useCallback, useState } from "react";
import { useTranslations } from "next-intl";
import { useBucket } from "@/lib/hooks/use-bucket";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Kanban, Smile } from "lucide-react";
import { toast } from "sonner";
import type { BucketKind } from "@/types/bucket";

interface BucketSettingsCardProps {
  kind: BucketKind;
  /** Title namespace, "bucket" for adult / "happyBucket" for happy. */
  titleNamespace: "bucket" | "happyBucket";
}

/** Settings card for a single Kanban board (max_in_progress). */
export function BucketSettingsCard({ kind, titleNamespace }: BucketSettingsCardProps) {
  const tBucket = useTranslations("bucket");
  const tTitle = useTranslations(titleNamespace);
  const tCommon = useTranslations("common");
  const tSettings = useTranslations("settings");
  const { settings, updateSettings } = useBucket(kind);

  const [draft, setDraft] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);

  const current = draft !== "" ? draft : String(settings.max_in_progress);

  const handleSave = useCallback(async () => {
    const value = parseInt(current, 10);
    if (Number.isNaN(value) || value < 1) {
      toast.error(tBucket("invalidMaxInProgress"));
      return;
    }
    setIsSaving(true);
    try {
      await updateSettings(value);
      setDraft("");
      toast.success(tSettings("saved"));
    } catch {
      toast.error(tSettings("saved"));
    } finally {
      setIsSaving(false);
    }
  }, [current, updateSettings, tBucket, tSettings]);

  const Icon = kind === "happy" ? Smile : Kanban;
  const iconBg =
    kind === "happy"
      ? "bg-pink-100 dark:bg-pink-900 text-pink-600 dark:text-pink-400"
      : "bg-fuchsia-100 dark:bg-fuchsia-900 text-fuchsia-600 dark:text-fuchsia-400";

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className={"p-2 rounded-lg " + iconBg}>
            <Icon className="size-5" />
          </div>
          <div>
            <CardTitle className="text-base">{tTitle("settingsTitle")}</CardTitle>
            <CardDescription>{tBucket("maxInProgressDescription")}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <Label htmlFor={`max-in-progress-${kind}`}>{tBucket("maxInProgress")}</Label>
          <div className="flex gap-2 items-center">
            <Input
              id={`max-in-progress-${kind}`}
              type="number"
              min={1}
              max={99}
              value={current}
              onChange={(e) => setDraft(e.target.value)}
              className="w-24"
            />
            <Button
              onClick={handleSave}
              disabled={
                isSaving ||
                draft === "" ||
                parseInt(draft, 10) === settings.max_in_progress
              }
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              {tCommon("save")}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
