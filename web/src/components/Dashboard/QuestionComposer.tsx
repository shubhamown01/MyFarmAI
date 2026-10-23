'use client';

import { useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  Camera,
  Image as ImageIcon,
  Loader2,
  Mic,
  Send,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSpeechRecognition } from '@/hooks/useSpeechRecognition';

const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const MAX_IMAGE_BYTES = 8 * 1024 * 1024;

export interface QuestionComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (question: string) => void | Promise<void>;
  isSubmitting?: boolean;
  disabled?: boolean;
  placeholder?: string;
  autoFocus?: boolean;
  compact?: boolean;
  inputId?: string;
}

interface Attachment {
  file: File;
  previewUrl: string;
}

function validateImage(file: File): string | null {
  if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
    return 'Choose a JPG, PNG, or WebP image.';
  }
  if (file.size > MAX_IMAGE_BYTES) {
    return 'Choose an image smaller than 8 MB.';
  }
  return null;
}

export function QuestionComposer({
  value,
  onChange,
  onSubmit,
  isSubmitting = false,
  disabled = false,
  placeholder = 'Ask your farming question...',
  autoFocus = false,
  compact = false,
  inputId = 'farming-question',
}: QuestionComposerProps) {
  const [attachment, setAttachment] = useState<Attachment | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const attachmentRef = useRef<Attachment | null>(null);

  const {
    isListening,
    transcript,
    interimTranscript,
    error: voiceError,
    startListening,
    stopListening,
    resetTranscript,
  } = useSpeechRecognition('en-IN');

  useEffect(() => {
    attachmentRef.current = attachment;
  }, [attachment]);

  useEffect(
    () => () => {
      if (attachmentRef.current) {
        URL.revokeObjectURL(attachmentRef.current.previewUrl);
      }
    },
    []
  );

  const applyFile = (file: File | undefined) => {
    if (!file) return;
    const validationError = validateImage(file);
    if (validationError) {
      setFileError(validationError);
      return;
    }

    if (attachment) URL.revokeObjectURL(attachment.previewUrl);
    setAttachment({ file, previewUrl: URL.createObjectURL(file) });
    setFileError(null);
    setFormError(null);
  };

  const removeAttachment = () => {
    if (attachment) URL.revokeObjectURL(attachment.previewUrl);
    setAttachment(null);
    setFileError(null);
    if (imageInputRef.current) imageInputRef.current.value = '';
    if (cameraInputRef.current) cameraInputRef.current.value = '';
  };

  const insertTranscript = () => {
    const clean = `${transcript} ${interimTranscript}`.trim();
    if (!clean) return;
    const nextValue = value.trim() ? `${value.trim()} ${clean}` : clean;
    onChange(nextValue);
    resetTranscript();
    textareaRef.current?.focus();
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (disabled || isSubmitting) return;

    if (attachment) {
      setFormError('Image questions are not connected to the assistant yet. Remove the image to send a text question.');
      return;
    }

    const clean = value.trim();
    if (!clean) {
      setFormError('Enter a question before sending.');
      textareaRef.current?.focus();
      return;
    }

    setFormError(null);
    void onSubmit(clean);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      handleSubmit(event);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={cn(
        'relative rounded-[16px] border border-outline bg-surface',
        'shadow-[0_18px_40px_-34px_rgba(11,27,43,0.45)]',
        compact ? 'p-3.5 sm:p-4' : 'p-4 sm:p-5',
      )}
      aria-label="Ask the MyFarmAI assistant"
      noValidate
    >
      <label htmlFor={inputId} className="sr-only">
        Ask your farming question
      </label>
      <textarea
        ref={textareaRef}
        id={inputId}
        value={value}
        onChange={(event) => {
          onChange(event.target.value);
          if (formError) setFormError(null);
        }}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        autoFocus={autoFocus}
        disabled={disabled}
        rows={compact ? 2 : 3}
        aria-invalid={Boolean(formError)}
        aria-describedby={formError ? `${inputId}-error` : `${inputId}-hint`}
        className={cn(
          'w-full resize-none border-0 bg-transparent p-0 text-on-surface',
          'placeholder:text-on-surface-disabled focus:outline-none focus:ring-0',
          compact ? 'min-h-[52px] text-[15px] leading-6 sm:text-base' : 'min-h-[78px] text-[16px] leading-7 sm:min-h-[92px] sm:text-[17px]',
          'disabled:cursor-not-allowed disabled:opacity-60',
        )}
      />

      <p id={`${inputId}-hint`} className="sr-only">
        Press Enter to send, or Shift and Enter to add a new line.
      </p>

      {attachment ? (
        <div className="mt-2 flex items-start gap-3 rounded-xl border border-outline bg-surface-container-low p-2.5">
          {/* Blob previews cannot use next/image's remote optimizer. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={attachment.previewUrl}
            alt={`Preview of ${attachment.file.name}`}
            className="h-14 w-14 flex-none rounded-lg border border-outline object-cover"
          />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-on-surface">{attachment.file.name}</p>
            <p className="mt-0.5 text-xs leading-5 text-on-surface-variant">
              Image analysis is not connected yet. Remove the image to send your text question.
            </p>
          </div>
          <button
            type="button"
            onClick={removeAttachment}
            className="inline-flex h-9 w-9 flex-none items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            aria-label="Remove attached image"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      ) : null}

      <div className={cn('flex flex-wrap items-center justify-between gap-3', compact ? 'mt-2' : 'mt-3')}>
        <div className="flex flex-wrap items-center gap-2">
          <input
            ref={imageInputRef}
            type="file"
            accept={ACCEPTED_IMAGE_TYPES.join(',')}
            className="hidden"
            onChange={(event) => {
              applyFile(event.target.files?.[0]);
              event.target.value = '';
            }}
            aria-hidden="true"
            tabIndex={-1}
          />
          <input
            ref={cameraInputRef}
            type="file"
            accept={ACCEPTED_IMAGE_TYPES.join(',')}
            capture="environment"
            className="hidden"
            onChange={(event) => {
              applyFile(event.target.files?.[0]);
              event.target.value = '';
            }}
            aria-hidden="true"
            tabIndex={-1}
          />

          <button
            type="button"
            onClick={() => imageInputRef.current?.click()}
            className="inline-flex min-h-10 items-center gap-2 rounded-[10px] border border-outline bg-surface px-3 py-2 text-[14px] font-semibold text-on-surface transition-colors hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 sm:px-3.5"
          >
            <ImageIcon className="h-[18px] w-[18px] text-on-surface-variant" aria-hidden="true" />
            Add Image
          </button>

          <button
            type="button"
            onClick={() => cameraInputRef.current?.click()}
            className="inline-flex min-h-10 items-center gap-2 rounded-[10px] border border-outline bg-surface px-3 py-2 text-[14px] font-semibold text-on-surface transition-colors hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 sm:px-3.5"
          >
            <Camera className="h-[18px] w-[18px] text-on-surface-variant" aria-hidden="true" />
            Take Photo
          </button>

          <button
            type="button"
            onClick={() => (isListening ? stopListening() : startListening())}
            aria-pressed={isListening}
            className={cn(
              'inline-flex min-h-10 items-center gap-2 rounded-[10px] border px-3 py-2 text-[14px] font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 sm:px-3.5',
              isListening
                ? 'border-error/30 bg-error-container text-on-error-container'
                : 'border-outline bg-surface text-on-surface hover:bg-surface-container-low',
            )}
          >
            <Mic className={cn('h-[18px] w-[18px]', isListening ? 'text-error' : 'text-on-surface-variant')} aria-hidden="true" />
            {isListening ? 'Listening…' : 'Voice'}
          </button>
        </div>

        <button
          type="submit"
          disabled={isSubmitting || disabled}
          className={cn(
            'ml-auto inline-flex flex-none items-center justify-center rounded-full bg-primary text-on-primary',
            'shadow-[0_10px_20px_-12px_rgba(4,119,74,0.75)] transition-all duration-fast',
            'hover:bg-primary-hover active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-60',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
            compact ? 'h-11 w-11' : 'h-[58px] w-[58px] sm:h-[64px] sm:w-[64px]',
          )}
          aria-label={isSubmitting ? 'Sending question' : 'Send question'}
          aria-busy={isSubmitting}
        >
          {isSubmitting ? (
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
          ) : (
            <Send className={compact ? 'h-5 w-5 -translate-x-px translate-y-px' : 'h-6 w-6 -translate-x-px translate-y-px'} aria-hidden="true" />
          )}
        </button>
      </div>

      {(fileError || formError) && (
        <div
          id={`${inputId}-error`}
          role="alert"
          className="mt-3 flex items-start gap-2 rounded-lg bg-error-container px-3 py-2 text-[13px] leading-5 text-on-error-container"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 flex-none" aria-hidden="true" />
          <span>{fileError || formError}</span>
        </div>
      )}

      {(isListening || transcript || voiceError) && (
        <div className="mt-3 rounded-xl border border-outline bg-surface-container-low p-3" aria-live="polite">
          <div className="flex items-start gap-2">
            <span
              className={cn(
                'mt-1.5 h-2 w-2 flex-none rounded-full',
                isListening ? 'bg-error' : 'bg-on-surface-disabled',
              )}
              aria-hidden="true"
            />
            <div className="min-w-0 flex-1">
              <p className="text-[13px] font-semibold text-on-surface">
                {isListening ? 'Listening…' : transcript ? 'Voice transcript' : 'Voice input'}
              </p>
              <p className="mt-1 text-[13px] leading-5 text-on-surface-variant">
                {errorText(voiceError, transcript, interimTranscript)}
              </p>
              {(transcript || interimTranscript) && (
                <div className="mt-2 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={insertTranscript}
                    className="inline-flex min-h-9 items-center rounded-lg border border-outline bg-surface px-3 text-[13px] font-semibold text-on-surface hover:bg-surface-container-high focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    Insert text
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (isListening) stopListening();
                      resetTranscript();
                    }}
                    className="inline-flex min-h-9 items-center rounded-lg px-3 text-[13px] font-semibold text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    Discard
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </form>
  );
}

function errorText(
  voiceError: string | null,
  transcript: string,
  interimTranscript: string,
) {
  if (voiceError) return voiceError;
  if (interimTranscript) return `“${interimTranscript}”`;
  if (transcript) return `“${transcript.trim()}”`;
  return 'Speak clearly into your microphone. Your browser will ask for permission the first time.';
}
