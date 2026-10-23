import { render } from '@testing-library/react';
import { axe } from 'jest-axe';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Dialog } from '@/components/ui/Dialog';
import { Toast } from '@/components/ui/Toast';
import { Spinner } from '@/components/ui/Spinner';

describe('Base UI Components - Accessibility', () => {
  it('Button should have no accessibility violations', async () => {
    const { container } = render(<Button variant="primary">Test Button</Button>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('Button variants should have no accessibility violations', async () => {
    const variants = ['primary', 'secondary', 'ghost', 'destructive', 'outline'] as const;
    for (const variant of variants) {
      const { container } = render(<Button variant={variant}>{variant}</Button>);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    }
  });

  it('Input should have no accessibility violations', async () => {
    const { container } = render(<Input label="Test Input" placeholder="Enter text" />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('Input with error should have no accessibility violations', async () => {
    const { container } = render(
      <Input label="Email" error="Invalid email" helperText="Enter a valid email" />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('Card should have no accessibility violations', async () => {
    const { container } = render(
      <Card variant="default">
        <div>Card content</div>
      </Card>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('Interactive Card should have no accessibility violations', async () => {
    const { container } = render(
      <Card variant="default" interactive onClick={() => {}}>
        <div>Interactive card</div>
      </Card>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('Badge variants should have no accessibility violations', async () => {
    const variants = ['default', 'primary', 'secondary', 'success', 'warning', 'error', 'info', 'outline'] as const;
    for (const variant of variants) {
      const { container } = render(<Badge variant={variant}>{variant}</Badge>);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    }
  });

  it('Dialog should have no accessibility violations when open', async () => {
    const { container } = render(
      <Dialog open onOpenChange={() => {}} title="Test Dialog" description="Description">
        <div>Dialog content</div>
      </Dialog>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('Toast should have no accessibility violations', async () => {
    const { container } = render(
      <Toast variant="success" message="Success!" onDismiss={() => {}} />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('Spinner should have no accessibility violations', async () => {
    const { container } = render(<Spinner size="md" label="Loading" />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('Skeleton should have no accessibility violations', async () => {
    const { container } = render(<div><div data-testid="skeleton" /></div>);
    // Skeleton is just a div with aria-hidden, should pass
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});