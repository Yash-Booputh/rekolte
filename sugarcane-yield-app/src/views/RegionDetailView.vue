<template>
  <ion-page>
    <!-- Activation overlay -->
    <div v-if="activating" class="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center">
      <div class="bg-white rounded-2xl p-8 shadow-2xl flex flex-col items-center gap-4 min-w-[280px]">
        <svg class="animate-spin h-10 w-10 text-primary" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
        </svg>
        <p class="text-primary font-bold text-lg">Switching Model</p>
        <p class="text-slate-500 text-sm text-center">Refreshing predictions for this region…</p>
      </div>
    </div>

    <div class="h-full overflow-y-auto bg-parchment text-slate-900 font-sans flex flex-col pb-14 md:pb-0">
      <NavBar />

      <main class="px-4 md:px-6 py-6 md:py-8 w-full">
        <!-- Header -->
        <div class="mb-8">
          <nav class="flex items-center gap-2 text-sm text-primary/60 mb-4 font-medium">
            <router-link to="/dashboard" class="hover:text-primary">Dashboard</router-link>
            <span class="material-symbols-outlined text-xs">chevron_right</span>
            <span class="text-primary font-bold">Region Detail</span>
          </nav>
          <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <h1 class="text-5xl font-black text-primary tracking-tight mb-3">{{ regionLabel(selectedRegion) }} Region</h1>
              <!-- Region pill selector -->
              <div class="flex flex-wrap gap-2 mb-3">
                <button
                  v-for="r in REGIONS" :key="r"
                  @click="selectedRegion = r"
                  class="px-4 py-1.5 rounded-full text-sm font-bold transition-all"
                  :class="selectedRegion === r
                    ? 'bg-primary text-white shadow-md shadow-primary/20'
                    : 'bg-white text-primary/60 border border-primary/15 hover:border-primary/40 hover:text-primary'"
                >{{ regionLabel(r) }}</button>
              </div>
              <p class="text-primary/60 text-lg">Agricultural Performance &amp; Predictive Intelligence</p>
            </div>
            <button
              class="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-white font-semibold shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-60"
              :disabled="predicting"
              @click="runPrediction"
            >
              <svg v-if="predicting" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
              <span v-else class="material-symbols-outlined text-xl">analytics</span>
              {{ predicting ? 'Running…' : 'Run Prediction' }}
            </button>
          </div>
        </div>

        <!-- Main Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">
          <!-- Yield Forecast Card -->
          <div class="lg:col-span-5 flex flex-col">
            <div class="bg-white rounded-xl p-8 border border-primary/10 shadow-sm relative overflow-hidden h-full">
              <h3 class="text-primary/70 font-bold uppercase tracking-wider text-xs mb-6">Yield Forecast (TCH)</h3>

              <div v-if="loadingPrediction" class="flex items-center justify-center py-8">
                <svg class="animate-spin h-8 w-8 text-primary" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
              </div>

              <div v-else class="space-y-8">
                <div>
                  <p class="text-sm font-medium text-primary/50 mb-1">Predicted TCH ({{ latestPrediction?.season ?? '—' }})</p>
                  <div class="flex items-baseline gap-3">
                    <span class="text-6xl font-black text-primary">{{ latestPrediction ? latestPrediction.predicted_tch.toFixed(1) : '—' }}</span>
                    <span class="text-xl font-bold text-accent">tons/ha</span>
                  </div>
                </div>
                <div class="flex items-center gap-8 py-6 border-y border-primary/5">
                  <div>
                    <p class="text-xs font-bold text-primary/40 uppercase mb-1">Actual TCH</p>
                    <p class="text-2xl font-bold text-slate-700">{{ latestPrediction?.actual_tch?.toFixed(1) ?? '—' }}</p>
                  </div>
                  <div class="w-px h-10 bg-primary/10"></div>
                  <div>
                    <p class="text-xs font-bold text-primary/40 uppercase mb-1">Model Used</p>
                    <p class="text-sm font-bold text-primary">{{ latestPrediction?.model_used ?? '—' }}</p>
                  </div>
                </div>
                <div v-if="activeModel" class="flex items-center gap-3 p-4 bg-accent/10 rounded-lg border border-accent/20">
                  <span class="material-symbols-outlined text-accent font-bold">verified_user</span>
                  <p class="text-sm text-primary/80 leading-snug">
                    <span class="font-bold">Active model R²: {{ activeModel.loso_r2.toFixed(4) }}</span><br/>
                    RMSE: {{ activeModel.loso_rmse.toFixed(4) }} · MAE: {{ activeModel.loso_mae.toFixed(4) }}
                  </p>
                </div>
                <div v-else class="text-sm text-slate-400 text-center py-2">No active model configured.</div>
              </div>
            </div>
          </div>

          <!-- Historical TCH Chart -->
          <div class="lg:col-span-7">
            <div class="bg-white rounded-xl p-8 border border-primary/10 shadow-sm h-full">
              <div class="flex items-center justify-between mb-8">
                <div>
                  <h3 class="text-xl font-bold text-primary">Historical TCH Trends</h3>
                  <p class="text-sm text-primary/60">18-Season Performance Analysis (2008–2025)</p>
                </div>
              </div>
              <div v-if="loadingHistory" class="flex items-center justify-center h-48">
                <svg class="animate-spin h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
              </div>
              <template v-else>
                <Line :data="chartData" :options="chartOptions" class="max-h-64" />
                <div class="mt-8 grid grid-cols-2 gap-4">
                  <div class="p-4 rounded-lg bg-parchment border border-primary/5">
                    <p class="text-xs font-bold text-primary/40 uppercase mb-1">Peak Performance</p>
                    <p class="text-lg font-bold text-primary">
                      {{ peakSeason.tch }} <span class="text-sm font-normal">TCH ({{ peakSeason.season }})</span>
                    </p>
                  </div>
                  <div class="p-4 rounded-lg bg-parchment border border-primary/5">
                    <p class="text-xs font-bold text-primary/40 uppercase mb-1">18-Season Avg</p>
                    <p class="text-lg font-bold text-primary">{{ seasonAvg }} <span class="text-sm font-normal">TCH</span></p>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>

        <!-- Model Switcher -->
        <div class="mb-6 bg-white rounded-xl p-6 border border-primary/10 shadow-sm">
          <h3 class="text-xs font-bold text-primary/50 uppercase tracking-wider mb-4">Active Prediction Model</h3>
          <div class="flex flex-wrap gap-3">
            <div
              v-for="m in models" :key="m._id"
              class="flex items-center gap-1 rounded-xl border transition-all"
              :class="m.is_active ? 'border-primary bg-primary text-white' : 'border-slate-200 bg-white text-slate-700'"
            >
              <button
                :disabled="activating || m.is_active"
                @click="activate(m._id)"
                class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all"
                :class="m.is_active ? 'cursor-default' : 'hover:bg-primary/5'"
              >
                <span class="material-symbols-outlined text-base">{{ m.type === 'XGBoost' ? 'bolt' : 'forest' }}</span>
                <div class="text-left">
                  <p class="font-bold text-sm leading-none">{{ m.type }}</p>
                  <p class="text-[11px] mt-0.5 opacity-70">LOSO R² {{ m.loso_r2.toFixed(4) }}</p>
                </div>
                <span v-if="m.is_active" class="ml-1 text-[10px] font-bold bg-white/20 px-2 py-0.5 rounded-full">Active</span>
                <span v-else class="ml-1 text-[10px] font-bold text-primary/60">Switch</span>
              </button>
              <button
                v-if="!m.is_active"
                @click="deleteM(m._id)"
                class="px-2 py-3 text-slate-400 hover:text-red-500 transition-colors"
                title="Delete model"
              >
                <span class="material-symbols-outlined text-base">delete</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Key Stats Row -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="bg-white rounded-xl p-6 border-b-4 border-primary shadow-sm">
            <div class="flex items-center gap-4 mb-4">
              <div class="size-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                <span class="material-symbols-outlined">map</span>
              </div>
              <div>
                <h4 class="text-xs font-bold text-primary/50 uppercase tracking-widest">Surface Harvested</h4>
                <p class="text-2xl font-black text-primary">
                  {{ latestHarvest?.surface_harvested ? latestHarvest.surface_harvested.toLocaleString() : '—' }}
                  <span class="text-sm font-bold opacity-60">Ha</span>
                </p>
              </div>
            </div>
          </div>
          <div class="bg-white rounded-xl p-6 border-b-4 border-accent shadow-sm">
            <div class="flex items-center gap-4 mb-4">
              <div class="size-12 rounded-lg bg-accent/10 flex items-center justify-center text-accent">
                <span class="material-symbols-outlined">factory</span>
              </div>
              <div>
                <h4 class="text-xs font-bold text-primary/50 uppercase tracking-widest">Cane Production</h4>
                <p class="text-2xl font-black text-primary">
                  {{ latestHarvest?.cane_production ? (latestHarvest.cane_production / 1000).toFixed(0) + 'K' : '—' }}
                  <span class="text-sm font-bold opacity-60">Tons</span>
                </p>
              </div>
            </div>
          </div>
          <div class="bg-white rounded-xl p-6 border-b-4 border-primary/40 shadow-sm">
            <div class="flex items-center gap-4 mb-4">
              <div class="size-12 rounded-lg bg-primary/5 flex items-center justify-center text-primary/60">
                <span class="material-symbols-outlined">science</span>
              </div>
              <div>
                <h4 class="text-xs font-bold text-primary/50 uppercase tracking-widest">Extraction Rate</h4>
                <p class="text-2xl font-black text-primary">
                  {{ latestHarvest?.extraction_rate ?? '—' }}
                  <span class="text-sm font-bold opacity-60">%</span>
                </p>
              </div>
            </div>
          </div>
        </div>

      </main>
      <FooterBar />
      <BottomTabBar />
    </div>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { IonPage, onIonViewWillEnter } from '@ionic/vue'
import { modelActivatedAt } from '@/stores/appState'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler,
} from 'chart.js'
import NavBar from '@/components/NavBar.vue'
import BottomTabBar from '@/components/BottomTabBar.vue'
import FooterBar from '@/components/FooterBar.vue'
import { getHarvest, getPredictions, runPrediction as apiRunPrediction, getModels, activateModel, deleteModel } from '@/services/api'
import type { HarvestRecord, PredictionRecord, ModelConfig } from '@/services/api'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const REGIONS = ['NORD', 'EST', 'SUD', 'OUEST', 'CENTRE']
const selectedRegion = ref('CENTRE')
const predicting = ref(false)
const activating = ref(false)
const loadingHistory = ref(true)
const loadingPrediction = ref(true)

const history = ref<HarvestRecord[]>([])
const predictions = ref<PredictionRecord[]>([])
const models = ref<ModelConfig[]>([])

const activeModel = computed(() => models.value.find(m => m.is_active) ?? null)

const latestPrediction = computed(() =>
  predictions.value.find(p =>
    p.region === selectedRegion.value &&
    (!activeModel.value || p.model_used === activeModel.value.type)
  ) ?? null
)

const latestHarvest = computed(() => {
  const rows = history.value.filter(h => h.region === selectedRegion.value)
  return rows.sort((a, b) => b.season - a.season)[0] ?? null
})

async function loadRegionData() {
  loadingHistory.value = true
  loadingPrediction.value = true
  try {
    const [harvest, preds] = await Promise.all([
      getHarvest({ region: selectedRegion.value }),
      getPredictions({ region: selectedRegion.value }),
    ])
    history.value = harvest
    predictions.value = preds

  } finally {
    loadingHistory.value = false
    loadingPrediction.value = false
  }
}

async function refresh() {
  models.value = await getModels()
  await loadRegionData()
}

onMounted(refresh)
onIonViewWillEnter(refresh)
watch(modelActivatedAt, refresh)

watch(selectedRegion, loadRegionData)

async function runPrediction() {
  predicting.value = true
  try {
    const result = await apiRunPrediction(selectedRegion.value)
    predictions.value = [result, ...predictions.value.filter(p => p.region !== selectedRegion.value)]
  } catch (e: any) {
    alert('Prediction failed: ' + e.message)
  } finally {
    predicting.value = false
  }
}

async function activate(id: string) {
  activating.value = true
  try {
    await activateModel(id)
    models.value = await getModels()
    await loadRegionData()
    modelActivatedAt.value = Date.now()
  } catch (e: any) {
    alert('Activation failed: ' + e.message)
  } finally {
    activating.value = false
  }
}

async function deleteM(id: string) {
  if (!confirm('Delete this model? This cannot be undone.')) return
  try {
    await deleteModel(id)
    models.value = await getModels()
  } catch (e: any) {
    alert('Delete failed: ' + e.message)
  }
}

const regionHistory = computed(() =>
  history.value.filter(h => h.region === selectedRegion.value).sort((a, b) => a.season - b.season)
)

const peakSeason = computed(() => {
  const sorted = [...regionHistory.value].sort((a, b) => b.tch - a.tch)
  return sorted[0] ?? { tch: 0, season: '—' }
})

const seasonAvg = computed(() => {
  const vals = regionHistory.value.map(h => h.tch)
  return vals.length ? (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1) : '—'
})

const chartData = computed(() => ({
  labels: regionHistory.value.map(h => h.season.toString()),
  datasets: [{
    label: 'TCH',
    data: regionHistory.value.map(h => h.tch),
    borderColor: '#2d5016',
    backgroundColor: 'rgba(45, 80, 22, 0.08)',
    borderWidth: 2.5,
    pointBackgroundColor: '#C8891A',
    pointBorderColor: '#ffffff',
    pointBorderWidth: 2,
    pointRadius: 4,
    tension: 0.35,
    fill: true,
  }],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#2d5016',
      callbacks: { label: (ctx: any) => ` ${ctx.parsed.y} TCH` },
    },
  },
  scales: {
    x: { grid: { display: false }, ticks: { font: { size: 10 }, color: '#94a3b8' } },
    y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { font: { size: 10 }, color: '#94a3b8' } },
  },
}

function regionLabel(id: string) {
  const labels: Record<string, string> = { NORD: 'Nord', EST: 'Est', SUD: 'Sud', OUEST: 'Ouest', CENTRE: 'Centre' }
  return labels[id] ?? id
}
</script>
