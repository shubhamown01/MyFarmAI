import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { axe } from 'jest-axe';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ApiError, apiClient } from '@/lib/api/client';
import type { CropPlan, CropPlanRevision, FarmSummary } from '@/lib/api/types';
import { CropPlanning } from '@/components/Crops/CropPlanning';

jest.mock('@/lib/api/client', () => {
  const actual = jest.requireActual('@/lib/api/client');
  return {
    ...actual,
    apiClient: {
      getFarms: jest.fn(),
      getCropPlans: jest.fn(),
      createCropPlan: jest.fn(),
      getCropPlan: jest.fn(),
      getCropPlanRevisions: jest.fn(),
      getCropCycles: jest.fn(),
      addCropPlanTask: jest.fn(),
      updateCropPlanTask: jest.fn(),
    },
  };
});

const mockGetFarms = apiClient.getFarms as jest.Mock;
const mockGetCropPlans = apiClient.getCropPlans as jest.Mock;
const mockCreateCropPlan = apiClient.createCropPlan as jest.Mock;
const mockGetCropPlan = apiClient.getCropPlan as jest.Mock;
const mockGetCropPlanRevisions = apiClient.getCropPlanRevisions as jest.Mock;
const mockGetCropCycles = apiClient.getCropCycles as jest.Mock;
const mockUpdateCropPlanTask = apiClient.updateCropPlanTask as jest.Mock;

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

const ASSUMPTIONS =
  'Milestones are estimates from generic growing-day ranges for the crop — variety, local climate and soil are not accounted for unless data exists.';

const plan: CropPlan = {
  id: '33333333-3333-3333-3333-333333333333',
  farm_id: farm.id,
  user_id: farm.owner_id,
  crop_cycle_id: null,
  variety: 'Lokwan wheat',
  planting_date: '2026-06-01',
  assumptions: ASSUMPTIONS,
  milestones: [
    { title: 'Sowing window', date: '2026-06-01', note: null },
    {
      title: 'Expected harvest window',
      date: '2026-10-15',
      note: 'Based on 120–135 growing days',
    },
  ],
  tasks: [
    {
      id: '44444444-4444-4444-4444-444444444441',
      title: 'Prepare seedbed',
      due_date: '2026-05-25',
      source: 'user',
      status: 'pending',
      created_at: '2026-11-01T08:00:00Z',
    },
    {
      id: '44444444-4444-4444-4444-444444444442',
      title: 'Old irrigation check',
      due_date: '2026-05-20',
      source: 'user',
      status: 'cancelled',
      created_at: '2026-11-01T08:00:00Z',
    },
  ],
  created_at: '2026-11-01T08:00:00Z',
  updated_at: '2026-11-01T08:00:00Z',
};

const revisions: CropPlanRevision[] = [
  {
    id: '55555555-5555-5555-5555-555555555555',
    changed_by: farm.owner_id,
    summary: 'plan created',
    snapshot: {},
    created_at: '2026-11-01T08:00:00Z',
  },
];

function renderCropPlanning() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <CropPlanning />
    </QueryClientProvider>
  );
}

async function openPlanDetail() {
  mockGetFarms.mockResolvedValue([farm]);
  mockGetCropPlans.mockResolvedValue([plan]);
  mockGetCropPlan.mockResolvedValue(plan);
  mockGetCropCycles.mockResolvedValue([]);

  renderCropPlanning();

  fireEvent.click(await screen.findByRole('button', { name: 'View plan' }));

  await screen.findByText('Assumptions');
  await waitFor(() => expect(screen.getByText(ASSUMPTIONS)).toBeInTheDocument());
}

describe('CropPlanning', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders the list of plans for the first farm', async () => {
    mockGetFarms.mockResolvedValue([farm]);
    mockGetCropPlans.mockResolvedValue([plan]);

    renderCropPlanning();

    expect(await screen.findByText('Lokwan wheat')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'View plan' })).toBeInTheDocument();
  });

  it('renders the no-plans empty state with a create CTA', async () => {
    mockGetFarms.mockResolvedValue([farm]);
    mockGetCropPlans.mockResolvedValue([]);

    renderCropPlanning();

    expect(await screen.findByText('No plans yet')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create plan/i })).toBeInTheDocument();
  });

  it('renders the no-farm empty state when the user has no farm', async () => {
    mockGetFarms.mockResolvedValue([]);

    renderCropPlanning();

    expect(await screen.findByText('No farm yet', {}, { timeout: 3000 })).toBeInTheDocument();
    expect(mockGetCropPlans).not.toHaveBeenCalled();
  });

  it('renders the same no-farm empty state when plans return 404 FARM_NOT_FOUND', async () => {
    mockGetFarms.mockResolvedValue([farm]);
    mockGetCropPlans.mockRejectedValue(
      new ApiError(404, 'farm not found', 'FARM_NOT_FOUND')
    );

    renderCropPlanning();

    expect(await screen.findByText('No farm yet', {}, { timeout: 3000 })).toBeInTheDocument();
  });

  it('shows an error state with a retry control when the request fails', async () => {
    mockGetFarms.mockResolvedValue([farm]);
    mockGetCropPlans.mockRejectedValue(new ApiError(0, 'Network error', 'NETWORK_ERROR'));

    renderCropPlanning();

    expect(await screen.findByRole('alert', {}, { timeout: 3000 })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('shows milestones and the assumptions text verbatim in the plan detail', async () => {
    await openPlanDetail();

    expect(screen.getByText('Sowing window')).toBeInTheDocument();
    expect(screen.getByText(/Expected harvest window/)).toBeInTheDocument();
    expect(
      screen.getByText(/Based on 120–135 growing days/)
    ).toBeInTheDocument();
  });

  it('creates a plan and opens its detail with the assumptions', async () => {
    mockGetFarms.mockResolvedValue([farm]);
    mockGetCropPlans.mockResolvedValue([]);
    mockCreateCropPlan.mockResolvedValue(plan);
    mockGetCropPlan.mockResolvedValue(plan);
    mockGetCropCycles.mockResolvedValue([]);

    renderCropPlanning();

    await screen.findByText('No plans yet');
    fireEvent.change(screen.getByLabelText('Variety'), {
      target: { value: 'Lokwan wheat' },
    });
    fireEvent.change(screen.getByLabelText('Planting date'), {
      target: { value: '2026-06-01' },
    });
    fireEvent.click(screen.getByRole('button', { name: /create plan/i }));

    await screen.findByText('Assumptions');
    expect(mockCreateCropPlan).toHaveBeenCalledWith(farm.id, {
      variety: 'Lokwan wheat',
      planting_date: '2026-06-01',
      crop_cycle_id: null,
      tasks: [],
    });
    expect(screen.getByText(ASSUMPTIONS)).toBeInTheDocument();
  });

  it('soft-cancels a pending task while cancelled tasks stay visible', async () => {
    mockUpdateCropPlanTask.mockResolvedValue({
      ...plan.tasks[0],
      status: 'cancelled',
      plan_id: plan.id,
    });

    await openPlanDetail();

    // A previously cancelled task is never deleted — it stays visible, marked.
    expect(screen.getByText('Old irrigation check')).toBeInTheDocument();
    expect(screen.getAllByText('cancelled').length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole('button', { name: 'Cancel task' }));

    await waitFor(() =>
      expect(mockUpdateCropPlanTask).toHaveBeenCalledWith(
        plan.id,
        plan.tasks[0].id,
        { status: 'cancelled' }
      )
    );
  });

  it('renders the revision history', async () => {
    mockGetCropPlanRevisions.mockResolvedValue(revisions);

    await openPlanDetail();

    fireEvent.click(
      screen.getByRole('button', { name: 'View revision history' })
    );

    expect(await screen.findByText('plan created')).toBeInTheDocument();
  });

  it('has no accessibility violations when plan data is rendered', async () => {
    await openPlanDetail();

    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });
});
