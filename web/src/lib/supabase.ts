/**
 * Safe client-side Supabase connector.
 * If SUPABASE_URL / SUPABASE_ANON_KEY are missing or unreachable, degrades cleanly to L8.
 */

export interface FeedbackSubmission {
  idempotencyKey: string
  deviceHash: string
  district: string
  cellId?: string | null
  fieldRef?: string | null
  runId: string
  feedbackType: string
  details?: Record<string, unknown>
}

// Generate or retrieve persistent anonymous device hash
export function getDeviceHash(): string {
  const KEY = 'prahari_device_hash'
  let hash = localStorage.getItem(KEY)
  if (!hash) {
    hash = 'dev_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
    localStorage.setItem(KEY, hash)
  }
  return hash
}

export async function submitFeedbackRemote(payload: FeedbackSubmission): Promise<{ ok: boolean; error?: string }> {
  const url = import.meta.env.VITE_SUPABASE_URL
  const key = import.meta.env.VITE_SUPABASE_ANON_KEY

  if (!url || !key) {
    // Graceful offline mock / degradation L8
    return { ok: true }
  }

  try {
    const res = await fetch(`${url}/rest/v1/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': key,
        'Authorization': `Bearer ${key}`,
        'Prefer': 'return=minimal',
      },
      body: JSON.stringify({
        idempotency_key: payload.idempotencyKey,
        device_hash: payload.deviceHash,
        district: payload.district,
        cell_id: payload.cellId,
        field_ref: payload.fieldRef,
        run_id: payload.runId,
        feedback_type: payload.feedbackType,
        details: payload.details || {},
      }),
    })

    if (!res.ok && res.status !== 409) {
      // 409 Conflict is acceptable because idempotency means it was already received
      return { ok: false, error: `HTTP ${res.status}` }
    }
    return { ok: true }
  } catch (err) {
    return { ok: false, error: String(err) }
  }
}
