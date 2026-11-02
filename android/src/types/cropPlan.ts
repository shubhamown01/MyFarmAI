// Mirrors backend/app/schemas/crop_plan.py — dates are YYYY-MM-DD strings,
// datetimes ISO strings. `assumptions` is always present in plan responses
// and must be rendered verbatim. Cancelled tasks are soft-cancelled and stay
// visible; they are never deleted.
export type PlanTaskStatus = 'pending' | 'done' | 'cancelled';
export type PlanTaskSource = 'user' | 'suggested';

export interface PlanTask {
  id: string;
  title: string;
  due_date: string | null;
  source: PlanTaskSource;
  status: PlanTaskStatus;
  created_at: string;
}

export interface PlanMilestone {
  title: string;
  date: string;
  note: string | null;
}

export interface CropPlan {
  id: string;
  farm_id: string;
  user_id: string;
  crop_cycle_id: string | null;
  variety: string | null;
  planting_date: string | null;
  assumptions: string | null;
  milestones: PlanMilestone[];
  tasks: PlanTask[];
  created_at: string;
  updated_at: string;
}

export interface CropPlanRevision {
  id: string;
  changed_by: string;
  summary: string;
  snapshot: Record<string, unknown>;
  created_at: string;
}

// Request payloads (subset of schemas/crop_plan.py create/update models).
export interface CropPlanCreateInput {
  crop_cycle_id?: string;
  variety?: string;
  planting_date?: string;
  tasks?: PlanTaskCreateInput[];
}

export interface CropPlanUpdateInput {
  crop_cycle_id?: string;
  variety?: string;
  planting_date?: string;
}

export interface PlanTaskCreateInput {
  title: string;
  due_date?: string;
}

export interface PlanTaskUpdateInput {
  title?: string;
  due_date?: string;
  status?: PlanTaskStatus;
}
