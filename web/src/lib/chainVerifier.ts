/**
 * In-browser Hash Chain Verifier (PRD §36).
 *
 * Verifies the append-only alert ledger directly in the visitor's browser using
 * Web Crypto API (SHA-256). Mirrors pipeline/ledger.py canonicalization exactly:
 * sort_keys=True, separators=(',', ':').
 */

export const GENESIS_HASH = 'sha256:' + '0'.repeat(64)
export const PREFIX = 'sha256:'

export interface LedgerEntry {
  seq: number
  timestamp: string
  cell_id: string
  model: string
  engine_sha: string
  band: string
  inputs_digest: string
  prev_hash: string
  hash: string
  [key: string]: unknown
}

export interface VerificationResult {
  ok: boolean
  count: number
  brokenAt?: number
  reason?: string
  entries: LedgerEntry[]
}

/**
 * Deterministically serialize a JS object to match Python's:
 * json.dumps(obj, sort_keys=True, separators=(',', ':'))
 */
export function canonicalJson(obj: unknown): string {
  if (obj === null || typeof obj !== 'object') {
    return JSON.stringify(obj)
  }

  if (Array.isArray(obj)) {
    return '[' + obj.map((item) => canonicalJson(item)).join(',') + ']'
  }

  const record = obj as Record<string, unknown>
  const sortedKeys = Object.keys(record).sort()
  const entries = sortedKeys.map((key) => {
    return JSON.stringify(key) + ':' + canonicalJson(record[key])
  })
  return '{' + entries.join(',') + '}'
}

/**
 * Compute SHA-256 hash matching pipeline/ledger.py compute_hash(record).
 */
export async function computeHash(record: Record<string, unknown>): Promise<string> {
  const body: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(record)) {
    if (key !== 'hash') {
      body[key] = value
    }
  }
  const canonical = canonicalJson(body)
  const encoder = new TextEncoder()
  const data = encoder.encode(canonical)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  const hex = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')
  return PREFIX + hex
}

/**
 * Verify a full JSONL ledger string in the browser.
 */
export async function verifyChain(jsonlContent: string): Promise<VerificationResult> {
  const lines = jsonlContent
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)

  if (lines.length === 0) {
    return { ok: true, count: 0, entries: [] }
  }

  const entries: LedgerEntry[] = []
  let prev = GENESIS_HASH

  for (let i = 0; i < lines.length; i++) {
    let rec: LedgerEntry
    try {
      rec = JSON.parse(lines[i])
    } catch {
      return { ok: false, count: i, brokenAt: i, reason: `Line ${i + 1} is invalid JSON`, entries }
    }

    if (rec.prev_hash !== prev) {
      return {
        ok: false,
        count: lines.length,
        brokenAt: i,
        reason: `Previous hash mismatch at line ${i + 1}: expected ${prev.slice(0, 16)}..., got ${(rec.prev_hash || '').slice(0, 16)}...`,
        entries,
      }
    }

    const expectedHash = await computeHash(rec)
    if (expectedHash !== rec.hash) {
      return {
        ok: false,
        count: lines.length,
        brokenAt: i,
        reason: `Hash mismatch at line ${i + 1}: computed ${expectedHash.slice(0, 16)}..., recorded ${(rec.hash || '').slice(0, 16)}...`,
        entries,
      }
    }

    prev = rec.hash
    entries.push(rec)
  }

  return { ok: true, count: entries.length, entries }
}
