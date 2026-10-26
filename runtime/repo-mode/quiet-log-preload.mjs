// DC 0.2.52 emits each logging notification in one complete stdout.write.
// This availability policy is not a security boundary or a generic MCP proxy.
// Unrecognised, malformed, fragmented and batched writes pass through unchanged.

const ownOption = `--import=${import.meta.url}`;
if (process.env.NODE_OPTIONS === ownOption) {
  // The preload belongs to the MCP server, not development commands it spawns.
  delete process.env.NODE_OPTIONS;
}

const originalWrite = process.stdout.write;
const hasOwn = Object.prototype.hasOwnProperty;

function isLoggingNotification(chunk, encoding) {
  if (encoding != null && typeof encoding !== 'string' && typeof encoding !== 'function') return false;
  if (typeof encoding === 'string' && !Buffer.isEncoding(encoding)) return false;
  if (typeof chunk !== 'string' && !Buffer.isBuffer(chunk)) return false;
  if (typeof chunk === 'string' && typeof encoding === 'string' &&
      !['utf8', 'utf-8'].includes(encoding.toLowerCase())) return false;

  const text = typeof chunk === 'string' ? chunk : chunk.toString('utf8');
  // Inspect only complete single-line messages, as written by the pinned DC.
  if (!text.endsWith('\n') || text.indexOf('\n') !== text.length - 1 ||
      !text.includes('"notifications/message"')) return false;
  try {
    const packet = JSON.parse(text);
    return packet !== null && typeof packet === 'object' && !Array.isArray(packet) &&
      packet.jsonrpc === '2.0' && packet.method === 'notifications/message' &&
      !hasOwn.call(packet, 'id');
  } catch {
    return false;
  }
}

process.stdout.write = function quietMcpLogs(chunk, encoding, callback) {
  if ((callback == null || typeof callback === 'function') &&
      isLoggingNotification(chunk, encoding)) {
    const done = typeof encoding === 'function' ? encoding : callback;
    if (typeof done === 'function') process.nextTick(done);
    return true;
  }
  // Preserve the original bytes, overloads, return value and backpressure.
  return Reflect.apply(originalWrite, this, arguments);
};
