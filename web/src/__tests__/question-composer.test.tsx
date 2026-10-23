import { useState } from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QuestionComposer } from '@/components/Dashboard/QuestionComposer';

jest.mock('@/hooks/useSpeechRecognition', () => ({
  useSpeechRecognition: () => ({
    isListening: false,
    isSupported: false,
    transcript: '',
    interimTranscript: '',
    language: 'en-IN',
    startListening: jest.fn(),
    stopListening: jest.fn(),
    resetTranscript: jest.fn(),
    setLanguage: jest.fn(),
    error: null,
  }),
}));

function Harness({ onSubmit }: { onSubmit: (question: string) => void }) {
  const [value, setValue] = useState('');
  return <QuestionComposer value={value} onChange={setValue} onSubmit={onSubmit} />;
}

describe('QuestionComposer', () => {
  beforeEach(() => {
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      writable: true,
      value: jest.fn(() => 'blob:preview'),
    });
    Object.defineProperty(URL, 'revokeObjectURL', {
      configurable: true,
      writable: true,
      value: jest.fn(),
    });
  });

  it('blocks an empty question with a visible error', () => {
    render(<Harness onSubmit={jest.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Send question' }));

    expect(screen.getByRole('alert')).toHaveTextContent('Enter a question before sending.');
  });

  it('submits a trimmed text question', async () => {
    const onSubmit = jest.fn();
    render(<Harness onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText('Ask your farming question'), {
      target: { value: '  How to improve wheat yield?  ' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Send question' }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith('How to improve wheat yield?'),
    );
  });

  it('does not send while an unsupported image is attached', () => {
    const onSubmit = jest.fn();
    const { container } = render(<Harness onSubmit={onSubmit} />);
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['leaf'], 'leaf.png', { type: 'image/png' });

    fireEvent.change(fileInput, { target: { files: [file] } });
    fireEvent.change(screen.getByLabelText('Ask your farming question'), {
      target: { value: 'What is wrong with this leaf?' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Send question' }));

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Image questions are not connected to the assistant yet.',
    );
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
