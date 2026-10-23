// P1-18/GAP-009 self-check: mirrors the base-url logic of src/config/api.ts.
// Jest is not installed in this package yet, so plain asserts stand in.
import assert from 'node:assert/strict';

const resolve = (env, dev) =>
  (env ??
    (dev
      ? 'http://10.0.2.2:8000/api/v1'
      : 'https://api.myfarmai.example.com/api/v1'))
    .replace(/\/?api\/v1\/?$/, '')
    .replace(/\/$/, '');

const endpoints = { chat: '/api/v1/chat', health: '/health' };

// default __DEV__ base + endpoint must compose to the exact backend URL
assert.equal(resolve(null, true) + endpoints.chat, 'http://10.0.2.2:8000/api/v1/chat');
// health lives outside /api/v1 on the backend
assert.equal(resolve(null, true) + endpoints.health, 'http://10.0.2.2:8000/health');
// env var wins, and an /api/v1 suffix is stripped so it is not doubled
assert.equal(resolve('http://192.168.1.100:8000/api/v1', true) + endpoints.chat, 'http://192.168.1.100:8000/api/v1/chat');
// already-origin values pass through untouched
assert.equal(resolve('http://10.0.2.2:8000', true) + endpoints.chat, 'http://10.0.2.2:8000/api/v1/chat');

console.log('check-api-url: all assertions passed');
