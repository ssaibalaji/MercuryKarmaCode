import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { FeeSummaryCard } from '../../../components/fees/FeeSummaryCard';
import { feeService } from '../../../services/feeService';
import { renderWithProviders } from '../../../test/test-utils';
import type { FeeDetailResponse, FeeStructureWithBalance } from '../../../types';

vi.mock('../../../services/feeService', () => ({
  feeService: {
    getFeeDetail: vi.fn(),
    createFeeStructure: vi.fn(),
    updateFeeStructure: vi.fn(),
    createRazorpayOrder: vi.fn(),
    getPaymentHistory: vi.fn(),
    sendReminder: vi.fn(),
    getOverdueFees: vi.fn(),
  },
}));

const mockedFeeService = vi.mocked(feeService);

function makeFeeStructure(
  overrides: Partial<FeeStructureWithBalance>,
): FeeStructureWithBalance {
  return {
    id: 1,
    student_id: 42,
    student_name: 'Jane Doe',
    amount: 1000,
    frequency: 'monthly',
    due_date: '2024-02-01',
    description: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    outstanding_balance: 1000,
    is_overdue: false,
    ...overrides,
  };
}

describe('FeeSummaryCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders total outstanding, no overdue badge, and the earliest unpaid due date', async () => {
    const detail: FeeDetailResponse = {
      student_id: 42,
      payments: [],
      total_outstanding: 3000,
      fee_structures: [
        makeFeeStructure({ id: 1, due_date: '2024-03-01', outstanding_balance: 1000 }),
        makeFeeStructure({ id: 2, due_date: '2024-02-01', outstanding_balance: 2000 }),
      ],
    };
    mockedFeeService.getFeeDetail.mockResolvedValue(detail);

    renderWithProviders(<FeeSummaryCard studentId={42} />);

    expect(await screen.findByText('₹3,000')).toBeInTheDocument();
    expect(screen.queryByText('Overdue')).not.toBeInTheDocument();
    expect(screen.getByText(/Next due: 2024-02-01 \(₹2,000\)/)).toBeInTheDocument();
  });

  it('renders the Overdue badge when a fee structure is overdue', async () => {
    const detail: FeeDetailResponse = {
      student_id: 42,
      payments: [],
      total_outstanding: 500,
      fee_structures: [
        makeFeeStructure({ id: 1, due_date: '2024-01-01', outstanding_balance: 500, is_overdue: true }),
      ],
    };
    mockedFeeService.getFeeDetail.mockResolvedValue(detail);

    renderWithProviders(<FeeSummaryCard studentId={42} />);

    expect(await screen.findByText('Overdue')).toBeInTheDocument();
  });

  it('renders an error message when the fee detail request fails', async () => {
    mockedFeeService.getFeeDetail.mockRejectedValue(new Error('boom'));

    renderWithProviders(<FeeSummaryCard studentId={42} />);

    expect(await screen.findByText('Unable to load fee summary.')).toBeInTheDocument();
  });
});
