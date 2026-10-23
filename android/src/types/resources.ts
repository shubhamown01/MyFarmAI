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

export interface ResourcesListRequest {
  category?: string;
}