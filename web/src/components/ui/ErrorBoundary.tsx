'use client';

import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, ChevronDown, ChevronUp, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './Button';

export interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  fallbackRender?: (error: Error, reset: () => void) => ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  showDetails: boolean;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = {
    hasError: false,
    error: null,
    showDetails: false,
  };

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }
    this.props.onError?.(error, errorInfo);
  }

  reset = (): void => {
    this.setState({ hasError: false, error: null, showDetails: false });
  };

  toggleDetails = (): void => {
    this.setState((prev) => ({ showDetails: !prev.showDetails }));
  };

  render(): ReactNode {
    const { hasError, error, showDetails } = this.state;
    const { children, fallback, fallbackRender } = this.props;

    if (!hasError) {
      return children;
    }

    if (fallbackRender && error) {
      return fallbackRender(error, this.reset);
    }

    if (fallback) {
      return fallback;
    }

    return (
      <div
        className={cn(
          'flex flex-col items-center justify-center gap-4 p-6',
          'bg-surface-container rounded-xl border border-outline',
          'text-center min-h-[200px] w-full'
        )}
        role="alert"
      >
        <div
          className={cn(
            'inline-flex items-center justify-center rounded-full',
            'bg-error-container text-on-error-container',
            'w-16 h-16 flex-shrink-0'
          )}
          aria-hidden="true"
        >
          <AlertTriangle className="w-8 h-8" />
        </div>

        <div className="space-y-2 w-full max-w-md">
          <h2 className={cn('text-lg font-semibold text-on-surface')}>
            Something went wrong
          </h2>
          <p className={cn('text-sm text-on-surface-variant')}>
            We ran into an unexpected error. Please try again or contact support
            if the problem persists.
          </p>
        </div>

        {process.env.NODE_ENV === 'development' && error && (
          <details className={cn('w-full max-w-md text-left')}>
            <summary
              className={cn(
                'flex items-center justify-between cursor-pointer',
                'text-sm text-on-surface-variant hover:text-on-surface',
                'select-none'
              )}
              onClick={(e) => {
                e.preventDefault();
                this.toggleDetails();
              }}
            >
              <span className="flex items-center gap-2">
                <span>Error Details</span>
                {showDetails ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </span>
            </summary>
            {showDetails && (
              <div className={cn(
                'mt-3 p-3 overflow-x-auto rounded-md',
                'bg-surface-container-highest border border-outline',
                'font-mono text-xs text-on-surface-variant'
              )}>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <strong>{error.name}</strong>
                  <button
                    onClick={this.toggleDetails}
                    className={cn(
                      'p-1 rounded hover:bg-surface-container',
                      'text-on-surface-variant hover:text-on-surface',
                      'flex-shrink-0'
                    )}
                    aria-label="Close error details"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
                <pre className="whitespace-pre-wrap break-words">{error.message}</pre>
                {error.stack && (
                  <pre className="mt-2 whitespace-pre-wrap break-words opacity-70">
                    {error.stack}
                  </pre>
                )}
              </div>
            )}
          </details>
        )}

        <Button
          variant="primary"
          size="md"
          onClick={this.reset}
          className="w-full max-w-xs"
        >
          <RefreshCw className="mr-2 w-4 h-4" aria-hidden="true" />
          Try Again
        </Button>
      </div>
    );
  }
}

export default ErrorBoundary;