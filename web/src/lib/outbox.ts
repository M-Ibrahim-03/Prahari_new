/**
 * Offline Outbox & Persistence Layer (PRD §28.3 L8/L9).
 *
 * Stores feedback, boundaries, and farmer modifications in localStorage / outbox.
 * Flushes queue to backend when online, deduplicating with idempotency keys.
 */

import { getDeviceHash, submitFeedbackRemote, type FeedbackSubmission } from './supabase'

const OUTBOX_KEY = 'prahari_outbox_queue'
const SAVED_FIELDS_KEY = 'prahari_custom_fields'

export interface OutboxItem {
  id: string // Idempotency UUID
  type: 'feedback' | 'field_boundary'
  payload: FeedbackSubmission | Record<string, unknown>
  createdAt: string
  attempts: number
}

export function getOutboxQueue(): OutboxItem[] {
  try {
    const raw = localStorage.getItem(OUTBOX_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function saveOutboxQueue(queue: OutboxItem[]): void {
  try {
    localStorage.setItem(OUTBOX_KEY, JSON.stringify(queue))
  } catch {
    // Storage full or unavailable
  }
}

export function queueFeedback(
  district: string,
  runId: string,
  feedbackType: string,
  cellId?: string | null,
  fieldRef?: string | null,
  details?: Record<string, unknown>,
): OutboxItem {
  const item: OutboxItem = {
    id: 'fdbk_' + Date.now() + '_' + Math.random().toString(36).substring(2, 8),
    type: 'feedback',
    payload: {
      idempotencyKey: 'fdbk_' + Date.now() + '_' + Math.random().toString(36).substring(2, 8),
      deviceHash: getDeviceHash(),
      district,
      cellId,
      fieldRef,
      runId,
      feedbackType,
      details,
    } as FeedbackSubmission,
    createdAt: new Date().toISOString(),
    attempts: 0,
  }

  const q = getOutboxQueue()
  q.push(item)
  saveOutboxQueue(q)

  // Try immediate sync in background
  flushOutbox()
  return item
}

export async function flushOutbox(): Promise<{ synced: number; remaining: number }> {
  if (!navigator.onLine) {
    return { synced: 0, remaining: getOutboxQueue().length }
  }

  const queue = getOutboxQueue()
  if (queue.length === 0) return { synced: 0, remaining: 0 }

  const remaining: OutboxItem[] = []
  let synced = 0

  for (const item of queue) {
    if (item.type === 'feedback') {
      const res = await submitFeedbackRemote(item.payload as FeedbackSubmission)
      if (res.ok) {
        synced++
      } else {
        item.attempts += 1
        if (item.attempts < 10) {
          remaining.push(item)
        }
      }
    } else {
      // Custom field or other types
      synced++
    }
  }

  saveOutboxQueue(remaining)
  return { synced, remaining: remaining.length }
}

// Attach listener for online reconnect
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    flushOutbox()
  })
}

// ── Custom Field Persistence (Phase E) ──────────────────────────

export interface CustomField {
  id: string
  name_hi: string
  name_en: string
  crop: string
  area_ha: number
  area_bigha: number
  coordinates: [number, number][] // [lat, lon]
  district: string
  createdAt: string
}

export function getCustomFields(): CustomField[] {
  try {
    const raw = localStorage.getItem(SAVED_FIELDS_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function saveCustomField(field: CustomField): void {
  const fields = getCustomFields()
  const existingIndex = fields.findIndex((f) => f.id === field.id)
  if (existingIndex >= 0) {
    fields[existingIndex] = field
  } else {
    fields.push(field)
  }
  try {
    localStorage.setItem(SAVED_FIELDS_KEY, JSON.stringify(fields))
  } catch {
    // ignore
  }
}
