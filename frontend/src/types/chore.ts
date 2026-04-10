export interface TimeWeightRule {
  hour: number;
  weight: number;
}

export interface WheelConfig {
  multiplicity: number;
  time_weight_rules: TimeWeightRule[];
}

export interface Chore {
  id: string;
  name: string;
  estimated_duration_minutes: number;
  category: string | null;
  wheel_config: WheelConfig;
  reward_value: string;
  created_at: string;
  updated_at: string;
}

export interface CreateChoreRequest {
  name: string;
  estimated_duration_minutes: number;
  category?: string;
  multiplicity?: number;
  time_weight_rules?: TimeWeightRule[];
  reward_value?: number;
}

export interface UpdateChoreRequest {
  name?: string;
  estimated_duration_minutes?: number;
  category?: string;
  multiplicity?: number;
  time_weight_rules?: TimeWeightRule[];
  reward_value?: number;
}
