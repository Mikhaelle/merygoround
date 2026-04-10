"use client";

import { useState, type FormEvent } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { TimeWeightEditor } from "./time-weight-editor";
import { Loader2 } from "lucide-react";
import type { Chore, CreateChoreRequest, TimeWeightRule } from "@/types/chore";

interface ChoreFormProps {
  chore?: Chore | null;
  onSubmit: (data: CreateChoreRequest) => Promise<void>;
  onCancel: () => void;
}

/** Form for creating or editing a chore with duration, category, multiplicity, and time weights. */
export function ChoreForm({ chore, onSubmit, onCancel }: ChoreFormProps) {
  const t = useTranslations("chores");
  const tCommon = useTranslations("common");

  const [name, setName] = useState(chore?.name ?? "");
  const [duration, setDuration] = useState<5 | 10>(
    chore?.estimated_duration_minutes === 10 ? 10 : 5,
  );
  const [category, setCategory] = useState(chore?.category ?? "");
  const [multiplicity, setMultiplicity] = useState(chore?.wheel_config.multiplicity ?? 1);
  const [timeWeightRules, setTimeWeightRules] = useState<TimeWeightRule[]>(
    chore?.wheel_config.time_weight_rules ?? [],
  );
  const [rewardValue, setRewardValue] = useState<number>(
    chore?.reward_value ? parseFloat(chore.reward_value) : 1.0,
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;

    setIsSubmitting(true);
    try {
      await onSubmit({
        name: name.trim(),
        estimated_duration_minutes: duration,
        category: category.trim() || undefined,
        multiplicity,
        time_weight_rules: timeWeightRules.length > 0 ? timeWeightRules : undefined,
        reward_value: rewardValue,
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="chore-name">{t("name")}</Label>
        <Input
          id="chore-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t("namePlaceholder")}
          required
        />
      </div>

      <div className="space-y-3">
        <Label>{t("duration")}</Label>
        <div className="flex gap-3">
          <Button
            type="button"
            variant={duration === 5 ? "default" : "outline"}
            className={duration === 5 ? "flex-1 bg-indigo-600 hover:bg-indigo-700 text-white" : "flex-1"}
            onClick={() => setDuration(5)}
          >
            5 {t("durationUnit")}
          </Button>
          <Button
            type="button"
            variant={duration === 10 ? "default" : "outline"}
            className={duration === 10 ? "flex-1 bg-indigo-600 hover:bg-indigo-700 text-white" : "flex-1"}
            onClick={() => setDuration(10)}
          >
            10 {t("durationUnit")}
          </Button>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="chore-category">{t("category")}</Label>
        <Input
          id="chore-category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          placeholder={t("categoryPlaceholder")}
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label>{t("multiplicity")}</Label>
          <span className="text-xs text-muted-foreground max-w-[60%] text-right">
            {t("multiplicityHelp")}
          </span>
        </div>
        <Input
          id="chore-multiplicity"
          type="number"
          min={1}
          value={multiplicity}
          onChange={(e) => setMultiplicity(Math.max(1, parseInt(e.target.value) || 1))}
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="chore-reward">{t("rewardValue")}</Label>
          <span className="text-xs text-muted-foreground max-w-[60%] text-right">
            {t("rewardValueHelp")}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-muted-foreground">R$</span>
          <Input
            id="chore-reward"
            type="number"
            min={0.01}
            max={10}
            step={0.01}
            value={rewardValue}
            onChange={(e) => {
              const v = parseFloat(e.target.value);
              if (!isNaN(v)) setRewardValue(Math.min(10, Math.max(0.01, v)));
            }}
          />
        </div>
      </div>

      <Separator />

      <TimeWeightEditor rules={timeWeightRules} onChange={setTimeWeightRules} />

      <div className="flex gap-3 pt-2">
        <Button type="button" variant="outline" className="flex-1" onClick={onCancel}>
          {tCommon("cancel")}
        </Button>
        <Button
          type="submit"
          className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white"
          disabled={isSubmitting || !name.trim()}
        >
          {isSubmitting && <Loader2 className="size-4 animate-spin" />}
          {tCommon("save")}
        </Button>
      </div>
    </form>
  );
}
