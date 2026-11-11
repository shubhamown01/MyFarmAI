import { render, screen } from '@testing-library/react';
import { TopBar } from '@/components/Layout/TopBar';

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), prefetch: jest.fn() }),
}));

describe('TopBar mobile navigation toggle', () => {
  it('exposes the drawer state as aria-expanded', () => {
    const { rerender } = render(<TopBar menuOpen={false} />);
    const button = screen.getByRole('button', { name: 'Open navigation menu' });
    expect(button).toHaveAttribute('aria-expanded', 'false');

    rerender(<TopBar menuOpen />);
    expect(screen.getByRole('button', { name: 'Open navigation menu' })).toHaveAttribute(
      'aria-expanded',
      'true',
    );
  });
});
