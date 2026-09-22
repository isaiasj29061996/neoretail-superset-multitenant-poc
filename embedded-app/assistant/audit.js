import crypto from "node:crypto";

function redact(value) {
  return String(value || "")
    .replace(/Bearer\s+[A-Za-z0-9._~-]+/gi, "Bearer [REDACTED]")
    .replace(/\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b/g, "[JWT_REDACTED]")
    .replace(/(password|secret|connection[_ -]?string|api[_ -]?key)\s*[:=]\s*\S+/gi, "$1=[REDACTED]")
    .slice(0, 500);
}

export function safeUserId(username, salt = "neoretail-assistant") {
  return crypto.createHash("sha256").update(`${salt}:${username}`).digest("hex").slice(0, 16);
}

export function auditEvent(event, logger = console) {
  const record = {
    event: "neoretail_assistant",
    timestamp: new Date().toISOString(),
    ...event,
    question: redact(event.question),
  };
  logger.info(JSON.stringify(record));
  return record;
}

export function newRequestId() {
  return crypto.randomUUID();
}
