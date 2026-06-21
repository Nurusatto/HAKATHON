export type blackList = {
  id: number;
  type: string;
  value: string;
  reason: string;
  is_active: boolean;
  created_at: string;
  action: () => void;
};
