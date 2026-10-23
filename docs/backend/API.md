# MyFarm AI Backend — API Reference

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.myfarmai.example.com`

All API routes are prefixed with `/api/v1`.

## Authentication

**Phase 0**: No authentication required (public prototype).

Future: JWT Bearer token in `Authorization` header.

## Endpoints

### 1. Root Information

**GET** `/`

Returns basic project information.

#### Response

```json
{
  "project": "My Farm AI",
  "version": "0.2.0",
  "status": "running"
}
```

**Status Codes**: 200 OK

---

### 2. Health Check (Root)

**GET** `/health`

Simple health check endpoint.

#### Response

```json
{
  "status": "ok",
  "service": "backend"
}
```

**Status Codes**: 200 OK

---

### 3. Health Check (Versioned)

**GET** `/api/v1/health`

Versioned health check endpoint.

#### Response

```json
{
  "status": "ok",
  "service": "backend"
}
```

**Status Codes**: 200 OK

---

### 4. Chat with AI Assistant

**POST** `/api/v1/chat`

Send a message to the agricultural AI assistant and receive a response. Supports conversation continuity.

#### Request Body

```json
{
  "message": "string (required, 1-2000 chars)",
  "conversation_id": "string (optional, UUID)",
  "language": "string (optional, ISO 639-1, default: 'en')",
  "crop": "string (optional, max 100 chars)",
  "location": "string (optional, max 200 chars)"
}
```

| Field | Required | Type | Constraints | Description |
|-------|----------|------|-------------|-------------|
| `message` | Yes | string | 1-2000 chars, non-empty | Farmer's question or message |
| `conversation_id` | No | string | UUID v4 format | Existing conversation to continue |
| `language` | No | string | 2-letter code (e.g., 'en', 'hi') | Response language |
| `crop` | No | string | max 100 chars | Current crop for context |
| `location` | No | string | max 200 chars | Farmer's location for localized advice |

#### Example Request

```json
{
  "message": "What fertilizer should I use for wheat in Punjab?",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "language": "en",
  "crop": "wheat",
  "location": "Punjab, India"
}
```

#### Success Response (200 OK)

```json
{
  "response": "For wheat in Punjab, the recommended fertilizer depends on soil type and local conditions. Generally: 1) Nitrogen: 120-150 kg/ha split in 3 doses... 2) Phosphorus: 60-80 kg/ha as basal... 3) Potassium: 40-60 kg/ha... Important: Get a soil test for precise recommendations. Consult your local Krishi Vigyan Kendra for region-specific advice.",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "model": "qwen3:4b"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | AI assistant's response |
| `conversation_id` | string | Conversation UUID (new or continued) |
| `model` | string | Ollama model used (e.g., "qwen3:4b") |

---

### 5. Weather Information

**GET** `/api/v1/weather`

Get current weather and 7-day forecast for a location using Open-Meteo.

#### Query Parameters

| Parameter | Required | Type | Constraints | Description |
|-----------|----------|------|-------------|-------------|
| `latitude` | Yes | float | -90.0 to 90.0 | Latitude in decimal degrees |
| `longitude` | Yes | float | -180.0 to 180.0 | Longitude in decimal degrees |
| `current` | No | bool | default: true | Include current weather |
| `daily` | No | bool | default: true | Include 7-day daily forecast |

#### Example Request

```
GET /api/v1/weather?latitude=28.6139&longitude=77.2090&current=true&daily=true
```

#### Success Response (200 OK)

```json
{
  "latitude": 28.6139,
  "longitude": 77.2090,
  "generationtime_ms": 0.427,
  "utc_offset_seconds": 19800,
  "timezone": "Asia/Kolkata",
  "timezone_abbreviation": "GMT+5:30",
  "elevation": 214.0,
  "current_weather": {
    "temperature": 28.5,
    "windspeed": 3.6,
    "winddirection": 333,
    "weathercode": 0,
    "weather_description": "Clear sky",
    "time": "2026-10-18T16:15"
  },
  "daily": [
    {
      "date": "2026-10-18",
      "temperature_2m_max": 28.8,
      "temperature_2m_min": 20.3,
      "precipitation_sum": 0.0,
      "precipitation_probability_max": 0,
      "weathercode": 0,
      "weather_description": "Clear sky"
    },
    {
      "date": "2026-10-19",
      "temperature_2m_max": 30.1,
      "temperature_2m_min": 21.0,
      "precipitation_sum": 2.5,
      "precipitation_probability_max": 30,
      "weathercode": 61,
      "weather_description": "Slight rain"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `latitude` | float | Requested latitude |
| `longitude` | float | Requested longitude |
| `generationtime_ms` | float | API response generation time |
| `utc_offset_seconds` | int | Timezone offset from UTC |
| `timezone` | string | IANA timezone identifier |
| `timezone_abbreviation` | string | Timezone abbreviation |
| `elevation` | float | Elevation in meters |
| `current_weather` | object | Current weather conditions |
| `daily` | array | 7-day forecast array |

#### Current Weather Object

| Field | Type | Description |
|-------|------|-------------|
| `temperature` | float | Air temperature at 2m in °C |
| `windspeed` | float | Wind speed at 10m in km/h |
| `winddirection` | int | Wind direction in degrees |
| `weathercode` | int | WMO weather condition code |
| `weather_description` | string | Human-readable weather description |
| `time` | string | Observation time in ISO 8601 |

#### Daily Forecast Object

| Field | Type | Description |
|-------|------|-------------|
| `date` | string | Date in YYYY-MM-DD |
| `temperature_2m_max` | float | Maximum temperature in °C |
| `temperature_2m_min` | float | Minimum temperature in °C |
| `precipitation_sum` | float | Total precipitation in mm |
| `precipitation_probability_max` | int | Max precipitation probability in % |
| `weathercode` | int | WMO weather condition code |
| `weather_description` | string | Human-readable weather description |

#### Weather Codes (WMO)

| Code | Description |
|------|-------------|
| 0 | Clear sky |
| 1 | Mainly clear |
| 2 | Partly cloudy |
| 3 | Overcast |
| 45 | Fog |
| 48 | Depositing rime fog |
| 51-57 | Drizzle (light to dense, freezing) |
| 61-67 | Rain (slight to heavy, freezing) |
| 71-77 | Snow fall (slight to heavy, grains) |
| 80-82 | Rain showers (slight to violent) |
| 85-86 | Snow showers (slight to heavy) |
| 95-99 | Thunderstorm (with/without hail) |

---

### 6. Current Weather Only

**GET** `/api/v1/weather/current`

Get only current weather (no forecast).

#### Query Parameters

| Parameter | Required | Type | Constraints | Description |
|-----------|----------|------|-------------|-------------|
| `latitude` | Yes | float | -90.0 to 90.0 | Latitude in decimal degrees |
| `longitude` | Yes | float | -180.0 to 180.0 | Longitude in decimal degrees |

#### Example Request

```
GET /api/v1/weather/current?latitude=28.6139&longitude=77.2090
```

#### Success Response (200 OK)

Same as weather response but with `daily` set to `null`.

---

### 7. Agricultural Resources

**GET** `/api/v1/resources`

Get curated list of agricultural resources for Indian farmers.

#### Query Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `category` | No | string | Filter by category (e.g., 'schemes', 'advisory', 'market', 'weather', 'research', 'financial', 'digital') |

#### Example Request

```
GET /api/v1/resources?category=schemes
```

#### Success Response (200 OK)

```json
{
  "resources": [
    {
      "title": "PM-KISAN - Pradhan Mantri Kisan Samman Nidhi",
      "category": "schemes",
      "url": "https://pmkisan.gov.in",
      "source": "Ministry of Agriculture & Farmers Welfare",
      "description": "Income support scheme providing Rs. 6000/year to eligible farmer families."
    },
    ...
  ],
  "total": 12,
  "categories": ["advisory", "digital", "financial", "market", "research", "schemes", "weather"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `resources` | array | Array of resource objects |
| `total` | int | Total number of resources returned |
| `categories` | array | List of all available categories |

#### Resource Object

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Resource title |
| `category` | string | Resource category |
| `url` | string | Resource URL |
| `source` | string | Source organization |
| `description` | string | Short factual description |

---

### 8. List Categories

**GET** `/api/v1/resources/categories`

Get list of all available resource categories.

#### Example Request

```
GET /api/v1/resources/categories
```

#### Success Response (200 OK)

```json
["advisory", "digital", "financial", "market", "research", "schemes", "weather"]
```

---

### 9. Resources by Category (Path Parameter)

**GET** `/api/v1/resources/{category}`

Get resources filtered by category via path parameter.

#### Path Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `category` | Yes | string | Category name (e.g., 'schemes', 'advisory') |

#### Example Request

```
GET /api/v1/resources/schemes
```

#### Success Response (200 OK)

Same structure as `/api/v1/resources` but filtered.

#### Error Response (404 Not Found)

```json
{
  "detail": "Category 'invalid' not found",
  "error_code": "CATEGORY_NOT_FOUND"
}
```

---

### Error Responses

All errors return a consistent structure:

```json
{
  "detail": "Human-readable error description",
  "error_code": "MACHINE_READABLE_CODE"
}
```

| Status | Error Code | Description |
|--------|------------|-------------|
| 400 | (Pydantic) | Request validation failed |
| 404 | CONVERSATION_NOT_FOUND | Conversation ID not found |
| 404 | CATEGORY_NOT_FOUND | Resource category not found |
| 422 | (Pydantic) | Request validation error |
| 429 | RATE_LIMIT_EXCEEDED | Rate limit exceeded |
| 503 | MODEL_NOT_FOUND | Ollama model not available |
| 503 | OLLAMA_CONNECTION_FAILED | Cannot reach Ollama service |
| 503 | WEATHER_CONNECTION_FAILED | Cannot reach weather service |
| 504 | OLLAMA_TIMEOUT | Ollama request timed out |
| 504 | WEATHER_TIMEOUT | Weather request timed out |
| 500 | INTERNAL_ERROR | Unexpected server error |

#### Example Error Response

```json
{
  "detail": "Conversation 550e8400-e29b-41d4-a716-446655440000 not found",
  "error_code": "CONVERSATION_NOT_FOUND"
}
```

---

### Conversation Management

[... rest of the document remains unchanged ...]