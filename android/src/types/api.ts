export interface ApiError extends Error {
  status: number;
  code?: string;
}

export interface HealthResponse {
  status: string;
  service: string;
}

export interface ErrorResponse {
  detail: string;
  error_code?: string;
}