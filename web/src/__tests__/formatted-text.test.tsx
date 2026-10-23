import { render, screen } from '@testing-library/react';
import { FormattedText } from '@/components/Chat/FormattedText';

describe('FormattedText', () => {
  it('renders bold markers as strong text without leaking asterisks', () => {
    render(<FormattedText text={'**Soil Health**\n- Add compost'} />);

    const bold = screen.getByText('Soil Health');
    expect(bold.tagName).toBe('STRONG');
    expect(screen.queryByText(/\*\*/)).not.toBeInTheDocument();
  });

  it('leaves unmatched asterisks as plain text', () => {
    render(<FormattedText text="Use ** only when paired" />);

    expect(screen.getByText('Use ** only when paired')).toBeInTheDocument();
  });
});
