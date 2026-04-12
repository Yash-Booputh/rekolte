<template>
  <ion-page>
    <div class="h-full overflow-y-auto bg-parchment text-slate-900 font-sans flex flex-col">
      <NavBar />

      <main class="w-full px-6 py-8">

        <!-- Page Header -->
        <div class="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10">
          <div class="space-y-2">
            <div class="flex items-center gap-2 text-primary font-semibold text-sm uppercase tracking-wider">
              <span class="material-symbols-outlined text-sm">compare_arrows</span>
              Model Performance Comparison
            </div>
            <h1 class="text-4xl font-black text-slate-900 tracking-tight">Random Forest vs. XGBoost</h1>
            <p class="text-slate-500 max-w-2xl text-lg">
              Evaluation using Leave-One-Season-Out cross-validation (18 seasons × 5 regions) and 2025 holdout test.
            </p>
          </div>
          <div class="flex bg-white p-1 rounded-xl shadow-sm border border-primary/10">
            <button
              @click="evalSet = 'loso'"
              :class="evalSet === 'loso' ? 'bg-primary text-white' : 'text-slate-500 hover:bg-primary/5'"
              class="px-6 py-2 rounded-lg text-sm font-bold transition-colors"
            >LOSO CV</button>
            <button
              @click="evalSet = 'test'"
              :class="evalSet === 'test' ? 'bg-primary text-white' : 'text-slate-500 hover:bg-primary/5'"
              class="px-6 py-2 rounded-lg text-sm font-bold transition-colors"
            >2025 Holdout</button>
          </div>
        </div>

        <div v-if="loading" class="flex items-center justify-center py-20">
          <svg class="animate-spin h-10 w-10 text-primary" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
        </div>

        <template v-else>
          <!-- Metric Cards -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
            <div class="bg-white rounded-xl p-6 shadow-sm border border-primary/10 relative overflow-hidden">
              <h3 class="text-slate-500 font-semibold text-sm mb-4">RMSE <span class="text-xs text-slate-400">(lower is better)</span></h3>
              <div class="flex items-center justify-between">
                <div class="space-y-1">
                  <p class="text-xs text-slate-400 uppercase font-bold">Random Forest</p>
                  <p class="text-2xl font-bold text-slate-600">{{ rfMetric('rmse') }}</p>
                </div>
                <div class="h-10 w-px bg-primary/10"></div>
                <div class="space-y-1 text-right">
                  <p class="text-xs text-primary uppercase font-bold">XGBoost</p>
                  <p class="text-3xl font-black text-primary">{{ xgbMetric('rmse') }}</p>
                </div>
              </div>
              <div class="mt-4 flex items-center gap-2 bg-primary/10 text-primary px-3 py-1.5 rounded-lg w-fit">
                <span class="material-symbols-outlined text-sm font-bold">verified</span>
                <span class="text-xs font-bold uppercase">XGBoost {{ rmseWinPct }}% better</span>
              </div>
            </div>

            <div class="bg-white rounded-xl p-6 shadow-sm border border-primary/10">
              <h3 class="text-slate-500 font-semibold text-sm mb-4">MAE <span class="text-xs text-slate-400">(lower is better)</span></h3>
              <div class="flex items-center justify-between">
                <div class="space-y-1">
                  <p class="text-xs text-slate-400 uppercase font-bold">Random Forest</p>
                  <p class="text-2xl font-bold text-slate-600">{{ rfMetric('mae') }}</p>
                </div>
                <div class="h-10 w-px bg-primary/10"></div>
                <div class="space-y-1 text-right">
                  <p class="text-xs text-primary uppercase font-bold">XGBoost</p>
                  <p class="text-3xl font-black text-primary">{{ xgbMetric('mae') }}</p>
                </div>
              </div>
              <div class="mt-4 flex items-center gap-2 bg-primary/10 text-primary px-3 py-1.5 rounded-lg w-fit">
                <span class="material-symbols-outlined text-sm font-bold">verified</span>
                <span class="text-xs font-bold uppercase">XGBoost {{ maeWinPct }}% better</span>
              </div>
            </div>

            <div class="bg-white rounded-xl p-6 shadow-sm border border-primary/10">
              <h3 class="text-slate-500 font-semibold text-sm mb-4">R² Score <span class="text-xs text-slate-400">(higher is better)</span></h3>
              <div class="flex items-center justify-between">
                <div class="space-y-1">
                  <p class="text-xs text-slate-400 uppercase font-bold">Random Forest</p>
                  <p class="text-2xl font-bold text-slate-600">{{ rfMetric('r2') }}</p>
                </div>
                <div class="h-10 w-px bg-primary/10"></div>
                <div class="space-y-1 text-right">
                  <p class="text-xs text-primary uppercase font-bold">XGBoost</p>
                  <p class="text-3xl font-black text-primary">{{ xgbMetric('r2') }}</p>
                </div>
              </div>
              <div class="mt-4 flex items-center gap-2 bg-primary/10 text-primary px-3 py-1.5 rounded-lg w-fit">
                <span class="material-symbols-outlined text-sm font-bold">verified</span>
                <span class="text-xs font-bold uppercase">XGBoost {{ r2WinPct }}% better</span>
              </div>
            </div>
          </div>

          <!-- Scatter: Predicted vs Actual (2025 holdout) -->
          <div class="bg-white rounded-xl p-8 shadow-sm border border-primary/10 mb-10">
            <div class="flex items-center justify-between mb-8">
              <div>
                <h2 class="text-xl font-bold text-slate-900">Predicted vs. Actual TCH (2025 Holdout)</h2>
                <p class="text-slate-500 text-sm">Each point = one region · Diagonal = perfect prediction</p>
              </div>
              <div class="flex items-center gap-6">
                <div class="flex items-center gap-2"><span class="size-3 rounded-full bg-slate-300"></span><span class="text-sm font-medium text-slate-600">Random Forest</span></div>
                <div class="flex items-center gap-2"><span class="size-3 rounded-full bg-primary"></span><span class="text-sm font-medium text-slate-600">XGBoost</span></div>
              </div>
            </div>
            <Scatter :data="scatterData" :options="scatterOptions" class="max-h-96" />
          </div>

          <!-- Feature Importance -->
          <div class="bg-white rounded-xl p-8 shadow-sm border border-primary/10 mb-10">
            <h2 class="text-xl font-bold text-slate-900 mb-2">Feature Importance Comparison</h2>
            <p class="text-slate-500 text-sm mb-8">Relative contribution of NDVI features and seasonal variables</p>
            <div class="space-y-5">
              <div v-for="feat in mergedFeatures" :key="feat.feature" class="space-y-1.5">
                <div class="flex justify-between text-sm font-bold">
                  <span class="text-slate-700">{{ feat.feature }}</span>
                  <span class="text-primary text-xs">XGB: {{ (feat.xgb * 100).toFixed(1) }}% · RF: {{ (feat.rf * 100).toFixed(1) }}%</span>
                </div>
                <div class="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden flex">
                  <div class="h-full bg-primary rounded-l-full" :style="`width: ${feat.xgb * 100}%`"></div>
                  <div class="h-full bg-slate-300/70" :style="`width: ${feat.rf * 100}%`"></div>
                </div>
              </div>
            </div>
          </div>

        </template>
      </main>

      <FooterBar />
    </div>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { IonPage } from '@ionic/vue'
import { Scatter } from 'vue-chartjs'
import { Chart as ChartJS, LinearScale, PointElement, LineElement, Tooltip, Legend } from 'chart.js'
import NavBar from '@/components/NavBar.vue'
import FooterBar from '@/components/FooterBar.vue'
import { getModels } from '@/services/api'
import type { ModelConfig } from '@/services/api'

ChartJS.register(LinearScale, PointElement, LineElement, Tooltip, Legend)

const loading = ref(true)
const evalSet = ref<'loso' | 'test'>('loso')
const models = ref<ModelConfig[]>([])

const rfModel  = computed(() => models.value.find(m => m.type === 'RandomForest'))
const xgbModel = computed(() => models.value.find(m => m.type === 'XGBoost'))

function rfMetric(key: string) {
  if (!rfModel.value) return '—'
  const prefix = evalSet.value === 'loso' ? 'loso_' : 'test_'
  return (rfModel.value as any)[prefix + key]?.toFixed(4) ?? '—'
}
function xgbMetric(key: string) {
  if (!xgbModel.value) return '—'
  const prefix = evalSet.value === 'loso' ? 'loso_' : 'test_'
  return (xgbModel.value as any)[prefix + key]?.toFixed(4) ?? '—'
}

const rmseWinPct = computed(() => {
  if (!rfModel.value || !xgbModel.value) return '—'
  const k = evalSet.value === 'loso' ? 'loso_rmse' : 'test_rmse'
  return (((rfModel.value as any)[k] - (xgbModel.value as any)[k]) / (rfModel.value as any)[k] * 100).toFixed(1)
})
const maeWinPct = computed(() => {
  if (!rfModel.value || !xgbModel.value) return '—'
  const k = evalSet.value === 'loso' ? 'loso_mae' : 'test_mae'
  return (((rfModel.value as any)[k] - (xgbModel.value as any)[k]) / (rfModel.value as any)[k] * 100).toFixed(1)
})
const r2WinPct = computed(() => {
  if (!rfModel.value || !xgbModel.value) return '—'
  const k = evalSet.value === 'loso' ? 'loso_r2' : 'test_r2'
  return (((xgbModel.value as any)[k] - (rfModel.value as any)[k]) / Math.abs((rfModel.value as any)[k]) * 100).toFixed(1)
})

const scatterData = computed((): any => {
  const rfPreds = rfModel.value?.holdout_predictions ?? []
  const xgbPreds = xgbModel.value?.holdout_predictions ?? []

  const allActual = [...rfPreds.map(p => p.actual_tch), ...xgbPreds.map(p => p.actual_tch)]
  const minV = allActual.length ? Math.min(...allActual) - 5 : 50
  const maxV = allActual.length ? Math.max(...allActual) + 5 : 100

  return {
    datasets: [
      {
        label: 'Perfect Prediction',
        data: [{ x: minV, y: minV }, { x: maxV, y: maxV }],
        type: 'line' as const,
        borderColor: 'rgba(200,137,26,0.6)',
        borderWidth: 1.5,
        borderDash: [6, 4],
        pointRadius: 0,
        fill: false,
        tension: 0,
      },
      {
        label: 'Random Forest',
        data: rfPreds.map(p => ({ x: p.actual_tch, y: p.rf_predicted })),
        backgroundColor: 'rgba(100,116,139,0.5)',
        pointRadius: 7,
        pointHoverRadius: 9,
      },
      {
        label: 'XGBoost',
        data: xgbPreds.map(p => ({ x: p.actual_tch, y: p.xgb_predicted })),
        backgroundColor: 'rgba(45,80,22,0.7)',
        pointRadius: 7,
        pointHoverRadius: 9,
        pointBorderColor: '#fff',
        pointBorderWidth: 1.5,
      },
    ],
  }
})

const scatterOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#2d5016',
      callbacks: {
        label: (ctx: any) => {
          if (ctx.dataset.label === 'Perfect Prediction') return ''
          return ` Actual: ${ctx.parsed.x} → Predicted: ${ctx.parsed.y}`
        },
      },
      filter: (item: any) => item.dataset.label !== 'Perfect Prediction',
    },
  },
  scales: {
    x: { title: { display: true, text: 'Actual TCH', color: '#94a3b8' }, grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#94a3b8' } },
    y: { title: { display: true, text: 'Predicted TCH', color: '#94a3b8' }, grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#94a3b8' } },
  },
}

// Hardcoded fallback — matches seed_models.py values (v3 pre-harvest, 39 features)
const FALLBACK_XGB_FI = [
  { feature: 'ndvi_may',           importance: 0.1394 },
  { feature: 'surface_prev',       importance: 0.1121 },
  { feature: 'ndvi_growth',        importance: 0.0785 },
  { feature: 'ndvi_jan_may_mean',  importance: 0.0719 },
  { feature: 'region_OUEST',       importance: 0.0624 },
  { feature: 'ndvi_lag_cumulative',importance: 0.0488 },
  { feature: 'ndvi_feb',           importance: 0.0487 },
  { feature: 'ndvi_lag_mean',      importance: 0.0456 },
  { feature: 'ndvi_lag_max',       importance: 0.0390 },
  { feature: 'rainfall_apr',       importance: 0.0357 },
  { feature: 'temp_lag_mean',      importance: 0.0351 },
  { feature: 'rainfall_may',       importance: 0.0308 },
  { feature: 'rainfall_nov',       importance: 0.0264 },
  { feature: 'ndvi_jan',           importance: 0.0207 },
  { feature: 'temp_feb',           importance: 0.0187 },
]
const FALLBACK_RF_FI: Record<string, number> = {
  ndvi_may: 0.0856, surface_prev: 0.2715, ndvi_growth: 0.0583,
  ndvi_jan_may_mean: 0.0577, region_OUEST: 0.0075,
  ndvi_lag_cumulative: 0.0150, ndvi_feb: 0.0923, ndvi_lag_mean: 0.0181,
  ndvi_lag_max: 0.0327, rainfall_apr: 0.0372, temp_lag_mean: 0.0216,
  rainfall_may: 0.0110, rainfall_nov: 0.0173, ndvi_jan: 0.0130, temp_feb: 0.0140,
}

const mergedFeatures = computed(() => {
  const xgbFI = xgbModel.value?.feature_importance?.length
    ? xgbModel.value.feature_importance
    : FALLBACK_XGB_FI
  const rfFI  = rfModel.value?.feature_importance ?? []
  return xgbFI.map((xf: any) => ({
    feature: xf.feature,
    xgb: xf.importance,
    rf: rfFI.find((r: any) => r.feature === xf.feature)?.importance
      ?? FALLBACK_RF_FI[xf.feature]
      ?? 0,
  })).sort((a, b) => b.xgb - a.xgb)
})

onMounted(async () => {
  models.value = await getModels()
  loading.value = false
})

</script>
