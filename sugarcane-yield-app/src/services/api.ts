const API_BASE = import.meta.env.VITE_API_URL || 'https://rekolte.onrender.com/api'

function getToken(): string | null {
  return localStorage.getItem('rekolte_token')
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  isFormData = false
): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (!isFormData) headers['Content-Type'] = 'application/json'

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: isFormData ? (body as FormData) : body ? JSON.stringify(body) : undefined,
  })

  if (res.status === 401) {
    localStorage.removeItem('rekolte_token')
    localStorage.removeItem('rekolte_user')
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || 'Request failed')
  }

  return res.json()
}

async function requestBlob(path: string, body: unknown): Promise<Blob> {
  const token = getToken()
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error('Report generation failed')
  return res.blob()
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authGoogle = (token: string) =>
  request<{ token: string; user: UserInfo }>('POST', '/auth/google', { idToken: token })

// ── Harvest ───────────────────────────────────────────────────────────────────
export const getHarvest = (params?: { region?: string; season?: number }) =>
  request<HarvestRecord[]>('GET', `/harvest${toQuery(params)}`)

// ── Predictions ───────────────────────────────────────────────────────────────
export const getLatestNdvi = () =>
  request<Record<string, NdviDoc>>('GET', '/ndvi/latest')

export const runPrediction = (region: string) =>
  request<PredictionRecord>('POST', '/predict', { region })

export const getPredictions = (params?: { region?: string; season?: number }) =>
  request<PredictionRecord[]>('GET', `/predictions${toQuery(params)}`)

// ── Models ────────────────────────────────────────────────────────────────────
export const getModels = () =>
  request<ModelConfig[]>('GET', '/models')

export const uploadModel = (formData: FormData) =>
  request<{ id: string }>('POST', '/models/upload', formData, true)

export const activateModel = (id: string) =>
  request<{ message: string }>('POST', `/models/${id}/activate`)

// ── Bulletins ─────────────────────────────────────────────────────────────────
export const getBulletins = (params?: { season?: number; type?: string }) =>
  request<BulletinDoc[]>('GET', `/bulletins${toQuery(params)}`)

export const uploadBulletin = (formData: FormData) =>
  request<{ id: string; driveFileId: string }>('POST', '/bulletins/upload', formData, true)

export const deleteBulletin = (id: string) =>
  request<{ message: string }>('DELETE', `/bulletins/${id}`)

// ── Notifications ─────────────────────────────────────────────────────────────
export const getNotifications = () =>
  request<Notification[]>('GET', '/notifications')

export const markNotificationRead = (id: string) =>
  request<{ message: string }>('POST', `/notifications/${id}/read`)

export const markAllNotificationsRead = () =>
  request<{ message: string }>('POST', '/notifications/read-all')

// ── Reports ───────────────────────────────────────────────────────────────────
export const generateReport = (data: { region?: string; season?: number }) =>
  requestBlob('/reports/generate', data)

// ── Helpers ───────────────────────────────────────────────────────────────────
function toQuery(params?: Record<string, unknown>): string {
  if (!params) return ''
  const q = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`)
    .join('&')
  return q ? `?${q}` : ''
}

// ── Types ─────────────────────────────────────────────────────────────────────
export interface UserInfo {
  email: string
  name: string
  picture: string
  role: string
}

export interface HarvestRecord {
  season: number
  region: string
  tch: number
  surface_harvested: number
  cane_production: number
  sugar_production: number | null
  extraction_rate: number | null
  tsh: number | null
}

export interface NdviDoc {
  region: string
  season: number
  ndvi_mean: number
  ndvi_max: number
  ndvi_cumulative: number
  observation_count: number
  extracted_at: string
}

export interface PredictionRecord {
  region: string
  season: number
  predicted_tch: number
  actual_tch: number | null
  model_used: string
  model_id: string
  created_by: string
  created_at: string
  ndvi_snapshot: {
    ndvi_mean: number
    ndvi_max: number
    ndvi_cumulative: number
    extracted_at: string
  }
}

export interface FeatureImportance {
  feature: string
  importance: number
}

export interface HoldoutPrediction {
  region: string
  actual_tch: number
  rf_predicted: number
  xgb_predicted: number
}

export interface ModelConfig {
  _id: string
  type: 'RandomForest' | 'XGBoost'
  filepath: string
  loso_r2: number
  loso_rmse: number
  loso_mae: number
  test_r2: number
  test_rmse: number
  test_mae: number
  r_squared: number
  rmse: number
  mae: number
  is_active: boolean
  uploaded_at: string
  feature_importance: FeatureImportance[]
  holdout_predictions: HoldoutPrediction[]
}

export interface BulletinDoc {
  _id: string
  filename: string
  driveFileId: string
  type: 'weekly' | 'crop_report' | 'other'
  season: number | null
  week: number | null
  uploaded_at: string
  uploaded_by: string
  preview_url: string
  download_url: string
}

export interface Notification {
  id: string
  type: 'prediction' | 'model_uploaded' | 'model_activated' | 'bulletin_uploaded'
  message: string
  metadata: Record<string, unknown>
  read: boolean
  created_at: string
}
