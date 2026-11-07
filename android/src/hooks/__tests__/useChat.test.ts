import { ApiError } from '../../lib/api/client';
import { friendlyChatError } from '../useChat';

describe('friendlyChatError (TEST-AUDIT High-5 regression)', () => {
  it.each([
    ['NETWORK_ERROR', 'offline'],
    ['NOT_AUTHENTICATED', 'session has expired'],
    ['UNAUTHORIZED', 'session has expired'],
    ['RATE_LIMIT_EXCEEDED', 'Too many requests'],
    ['AI_QUOTA_EXCEEDED', 'limit reached'],
    ['AI_BUSY', 'busy'],
    ['AI_UNAVAILABLE', 'busy'],
    ['AI_QUOTA_UNAVAILABLE', 'temporarily unavailable'],
  ])('maps %s to farmer language', (code, expected) => {
    const message = friendlyChatError(new ApiError(429, code, code));
    expect(message.toLowerCase()).toContain(expected.toLowerCase());
  });

  it('falls through to server message for unmapped codes', () => {
    const message = friendlyChatError(
      new ApiError(422, 'Email is not valid', 'VALIDATION_ERROR'),
    );
    expect(message).toBe('Email is not valid');
  });

  it('never leaks raw code/message formatting for unknown errors', () => {
    expect(friendlyChatError(new Error('Something went wrong'))).toBe(
      'Failed to send message. Please try again.',
    );
    expect(friendlyChatError(undefined)).toBe(
      'Failed to send message. Please try again.',
    );
  });
});
