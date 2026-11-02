export interface ChatRequest {
  message: string;
  conversation_id?: string;
  language?: string;
  crop?: string;
  location?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  conversationId: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  model: string;
}

export interface CurrentWeather {
  temperature: number;
  windspeed: number;
  winddirection: number;
  weathercode: number;
  weather_description: string;
  time: string;
}

export interface DailyForecast {
  date: string;
  temperature_2m_max: number;
  temperature_2m_min: number;
  precipitation_sum: number;
  precipitation_probability_max: number;
  weathercode: number;
  weather_description?: string;
}

export interface WeatherResponse {
  latitude: number;
  longitude: number;
  generationtime_ms: number;
  utc_offset_seconds: number;
  timezone: string;
  timezone_abbreviation: string;
  elevation: number;
  current_weather?: CurrentWeather;
  daily?: DailyForecast[];
}

export interface AgriculturalResource {
  title: string;
  category: string;
  url: string;
  source: string;
  description: string;
}

export interface ResourcesResponse {
  resources: AgriculturalResource[];
  total: number;
  categories: string[];
}

export interface ErrorResponse {
  detail: string;
  error_code?: string;
}

export interface HealthResponse {
  status: string;
  service: string;
}

// ---------------------------------------------------------------------------
// Dashboard (Phase 7A) — mirrors backend/app/schemas/dashboard.py.
// Every block carries `available` + `updated_at`; blocks that can fail carry
// an explicit `unavailable_reason`. Missing data is shown as missing, never
// fabricated (DEPENDENCY_POLICY rule 6).
// ---------------------------------------------------------------------------

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

// Minimal shape of GET /farms items (mirrors backend FarmResponse).
export interface FarmSummary {
  id: string;
  name: string;
  description: string | null;
  address: string | null;
  latitude: number | null;
  longitude: number | null;
  timezone: string;
  owner_id: string;
  is_active: boolean;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Crop planning (Phase 7B) — mirrors backend/app/schemas/crop_plan.py.
// Milestones are estimates; `assumptions` must be displayed verbatim.
// ---------------------------------------------------------------------------

export type PlanTaskStatus = 'pending' | 'done' | 'cancelled';
export type PlanTaskSource = 'user' | 'suggested';

export interface CropPlanTask {
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
  tasks: CropPlanTask[];
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

export interface CropPlanCreatePayload {
  crop_cycle_id?: string | null;
  variety?: string | null;
  planting_date?: string | null;
  tasks?: { title: string; due_date?: string | null }[];
}

export interface CropPlanTaskUpdatePayload {
  title?: string;
  due_date?: string | null;
  status?: PlanTaskStatus;
}

// Minimal shape of GET /farms/{farm_id}/crop-cycles items for plan creation
// (mirrors backend CropCycleResponse; crop name is not part of the response).
export interface CropCycleSummary {
  id: string;
  season_name: string | null;
  season_year: number;
  status: string;
  planting_date: string | null;
}