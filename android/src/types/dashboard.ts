// Mirrors backend/app/schemas/dashboard.py — every block carries
// `available` + `updated_at`; failing blocks carry `unavailable_reason`.
// Backend serializes datetimes as ISO strings and dates as YYYY-MM-DD.

export interface FarmBlock {
  available: boolean;
  updated_at: string;
  name: string;
  timezone: string;
  address: string | null;
  latitude: number | null;
  longitude: number | null;
}

export interface CropItem {
  crop: string;
  status: string;
  season_year: number;
  planting_date: string | null;
  expected_harvest_date: string | null;
}

export interface CropsBlock {
  available: boolean;
  updated_at: string;
  cycles: CropItem[];
  unavailable_reason: string | null;
}

export interface WeatherBlock {
  available: boolean;
  updated_at: string;
  temperature: number | null;
  windspeed: number | null;
  conditions: string | null;
  unavailable_reason: string | null;
}

export interface TaskItem {
  title: string;
  due_date: string;
  crop: string;
}

export interface TasksBlock {
  available: boolean;
  updated_at: string;
  items: TaskItem[];
  unavailable_reason: string | null;
}

export interface AlertItem {
  severity: string;
  message: string;
}

export interface AlertsBlock {
  available: boolean;
  updated_at: string;
  items: AlertItem[];
}

export interface RecommendationsBlock {
  available: boolean;
  unavailable_reason: string;
}

export interface ActivityItem {
  event_type: string;
  description: string | null;
  occurred_at: string;
}

export interface ActivityBlock {
  available: boolean;
  updated_at: string;
  items: ActivityItem[];
  unavailable_reason: string | null;
}

export interface DashboardResponse {
  farm_id: string;
  generated_at: string;
  farm: FarmBlock;
  crops: CropsBlock;
  weather: WeatherBlock;
  tasks: TasksBlock;
  alerts: AlertsBlock;
  recommendations: RecommendationsBlock;
  activity: ActivityBlock;
}

// Subset of backend/app/schemas/farm.py FarmResponse used for farm selection.
export interface FarmSummary {
  id: string;
  name: string;
  timezone: string;
  address: string | null;
}
