import { makeId } from '../id';

describe('makeId (Hermes-safe UUID, TEST-AUDIT High-3)', () => {
  it('matches UUID v4 format', () => {
    const id = makeId();
    expect(id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
    );
  });

  it('produces unique values across many calls', () => {
    const set = new Set(Array.from({ length: 1000 }, makeId));
    expect(set.size).toBe(1000);
  });

  it('stays within the backend request_id column limit (String(100))', () => {
    expect(makeId().length).toBeLessThanOrEqual(36);
  });
});
