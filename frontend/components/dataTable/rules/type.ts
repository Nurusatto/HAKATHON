export type Rules = {
  id: number;
  created_at: string;
  event_type: string;
  risk_weight: string;
  description: string;
  is_active: boolean;
};

export type ToggleActivePayload = {
  id: number;
  isActive: boolean;
};
