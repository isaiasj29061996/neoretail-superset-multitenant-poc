import assert from "node:assert/strict";
import test from "node:test";
import { auditEvent, safeUserId } from "../audit.js";

test("audit pseudonymizes users deterministically without storing usernames", () => {
  const first = safeUserId("analyst@example.com", "test-salt");
  const second = safeUserId("analyst@example.com", "test-salt");

  assert.equal(first, second);
  assert.equal(first.length, 16);
  assert.doesNotMatch(first, /analyst|example/i);
});

test("audit redacts credentials and tokens from questions", () => {
  let serialized;
  const logger = { info(value) { serialized = value; } };
  const record = auditEvent({
    userId: safeUserId("user"),
    question: "Bearer token.value password=hunter2 api_key=abc connection_string=postgres://secret",
  }, logger);

  assert.match(record.question, /Bearer \[REDACTED\]/);
  assert.match(record.question, /password=\[REDACTED\]/i);
  assert.match(record.question, /api_key=\[REDACTED\]/i);
  assert.match(record.question, /connection_string=\[REDACTED\]/i);
  assert.doesNotMatch(serialized, /hunter2|postgres:\/\/secret|token\.value/);
});
