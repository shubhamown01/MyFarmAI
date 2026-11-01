import { render, screen, waitFor } from '@testing-library/react';
import { axe } from 'jest-axe';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ApiError, apiClient } from '@/lib/api/client';
import type { DashboardResponse, FarmSummary } from '@/lib/api/types';
import { FarmIntelligence } from '@/components/Dashboard/FarmIntelligence';

jest.mock('@/lib/api/client', () => {
  const actual = jest.requireActual('@/lib/api/client');
  return {
    ...actual,
    apiClient: {
      getFarms: jest.fn(),
      getDashboard: jest.fn(),
    },
  };
});

const mockGetFarms = apiClient.getFarms as jest.Mock;
const mockGetDashboard = apiClient.getDashboard as jest.Mock;

const farm: FarmSummary = {
  id: '11111111-1111-1111-1111-111111111111',
  name: 'Green Acres',
  description: null,
  address: 'Durg, CG',
  latitude: 21.19,
  longitude: 81.35,
  timezone: 'Asia/Kolkata',
  owner_id: '22222222-2222-2222-2222-222222222222',
  is_active: true,
  created_at: '2026-10-01T00:00:00Z',
};

const dashboardData: DashboardResponse = {
  farm_id: farm.id,
  generated_at: '2026-11-01T08:00:00Z',
  farm: {
    available: true,
    updated_at: '2026-11-01T08:00:00Z',
    name: 'Green Acres',
    timezone: 'Asia/Kolkata',
    address: 'Durg, CG',
    latitude: 21.19,
    longitude: 81.35,
  },
  crops: {
    available: true,
    updated_at: '2026-11-01T08:00:00Z',
    cycles: [
      {
        crop: 'Wheat',
        status: 'active',
        season_year: 2026,
        planting_date: '2026-06-01',
        expected_harvest_date: '2026-10-15',
      },
    ],
    unavailable_reason: null,
  },
  weather: {
    available: true,
    updated_at: '2026-11-01T08:00:00Z',
    temperature: 28.4,
    windspeed: 11.2,
    conditions: 'Partly cloudy',
    unavailable_reason: null,
  },
  tasks: {
    available: true,
    updated_at: '2026-11-01T08:00:00Z',
    items: [{ title: 'Check irrigation', due_date: '2026-11-03', crop: 'Wheat' }],
    unavailable_reason: null,
  },
  alerts: {
    available: true,
    updated_at: '2026-11-01T08:00:00Z',
    items: [],
  },
  recommendations: {
    available: false,
    unavailable_reason: 'Saved recommendations are not available yet',
  },
  activity: {
    available: true,
    updated_at: '2026-11-01T08:00:00Z',
    items: [],
    unavailable_reason: null,
  },
};

function renderDashboard() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <FarmIntelligence />
    </QueryClientProvider>
  );
}

describe('FarmIntelligence', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders the farm name and live blocks', async () => {
    mockGetFarms.mockResolvedValue([farm]);
    mockGetDashboard.mockResolvedValue(dashboardData);

    renderDashboard();

    expect(await screen.findByText('Green Acres')).toBeInTheDocument();
    expect(screen.getByText(/Partly cloudy/)).toBeInTheDocument();
    expect(screen.getByText('Wheat')).toBeInTheDocument();
    expect(screen.getByText('Check irrigation')).toBeInTheDocument();
    expect(screen.getAllByText(/Last updated/).length).toBeGreaterThan(0);
  });

  it('renders an unavailable weather block with its reason', async () => {
    mockGetFarms.mockResolvedValue([farm]);
    mockGetDashboard.mockResolvedValue({
      ...dashboardData,
      weather: {
        ...dashboardData.weather,
        available: false,
        temperature: null,
        windspeed: null,
        conditions: null,
        unavailable_reason: 'Weather data is unavailable because the provider could not be reached.',
      },
    });

    renderDashboard();

    expect(await screen.findByText('Green Acres')).toBeInTheDocument();
    expect(
      screen.getByText('Weather data is unavailable because the provider could not be reached.')
    ).toBeInTheDocument();
  });

  it('renders a friendly empty state when the user has no farm', async () => {
    mockGetFarms.mockResolvedValue([]);

    renderDashboard();

    expect(await screen.findByText('No farm yet', {}, { timeout: 3000 })).toBeInTheDocument();
    expect(mockGetDashboard).not.toHaveBeenCalled();
  });

  it('renders the same empty state when the dashboard returns 404 FARM_NOT_FOUND', async () => {
    mockGetFarms.mockResolvedValue([farm]);
    mockGetDashboard.mockRejectedValue(
      new ApiError(404, 'farm not found', 'FARM_NOT_FOUND')
    );

    renderDashboard();

    expect(await screen.findByText('No farm yet', {}, { timeout: 3000 })).toBeInTheDocument();
  });

  it('shows an error state with a retry control when the request fails', async () => {
    mockGetFarms.mockResolvedValue([farm]);
    mockGetDashboard.mockRejectedValue(new ApiError(0, 'Network error', 'NETWORK_ERROR'));

    renderDashboard();

    expect(await screen.findByRole('alert', {}, { timeout: 3000 })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('has no accessibility violations when data is rendered', async () => {
    mockGetFarms.mockResolvedValue([farm]);
    mockGetDashboard.mockResolvedValue(dashboardData);

    const { container } = renderDashboard();
    await screen.findByText('Green Acres');
    await waitFor(() => expect(screen.getAllByText(/Last updated/).length).toBeGreaterThan(0));

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
