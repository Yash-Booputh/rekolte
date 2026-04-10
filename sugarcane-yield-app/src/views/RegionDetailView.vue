<template>
  <ion-page>
    <div class="h-full overflow-y-auto bg-parchment text-slate-900 font-sans flex flex-col">
      <NavBar />

      <main class="px-6 py-8 w-full">
        <!-- Header -->
        <div class="mb-8">
          <nav class="flex items-center gap-2 text-sm text-primary/60 mb-4 font-medium">
            <router-link to="/dashboard" class="hover:text-primary">Dashboard</router-link>
            <span class="material-symbols-outlined text-xs">chevron_right</span>
            <span class="text-primary font-bold">Region Detail</span>
          </nav>
          <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <div class="flex items-center gap-3 mb-2">
                <h1 class="text-5xl font-black text-primary tracking-tight">{{ regionLabel(selectedRegion) }} Region</h1>
                <select
                  v-model="selectedRegion"
                  class="ml-4 border border-primary/20 rounded-lg px-3 py-1.5 text-sm font-semibold text-primary bg-white focus:ring-2 focus:ring-primary/20"
                >
                  <option v-for="r in REGIONS" :key="r" :value="r">{{ regionLabel(r) }}</option>
                </select>
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
          <div class="lg:col-span-5">
            <div class="bg-white rounded-xl p-8 border border-primary/10 shadow-sm relative overflow-hidden">
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

        <footer class="mt-12 pt-8 border-t border-primary/10 flex justify-between items-center opacity-60">
          <p class="text-xs font-medium">Data: Mauritius Chamber of Agriculture Harvest Bulletins 2008–2025</p>
          <div class="flex gap-6 text-xs font-bold uppercase tracking-widest">
            <router-link to="/history" class="hover:text-primary">Full History</router-link>
            <router-link to="/compare" class="hover:text-primary">Compare Models</router-link>
          </div>
        </footer>
      </main>
    </div>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { IonPage } from '@ionic/vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler,
} from 'chart.js'
import NavBar from '@/components/NavBar.vue'
import { getHarvest, getPredictions, runPrediction as apiRunPrediction, getModels } from '@/services/api'
import type { HarvestRecord, PredictionRecord, ModelConfig } from '@/services/api'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const REGIONS = ['NORD', 'EST', 'SUD', 'OUEST', 'CENTRE']
const selectedRegion = ref('CENTRE')
const predicting = ref(false)
const loadingHistory = ref(true)
const loadingPrediction = ref(true)

const history = ref<HarvestRecord[]>([])
const predictions = ref<PredictionRecord[]>([])
const models = ref<ModelConfig[]>([])

const activeModel = computed(() => models.value.find(m => m.is_active) ?? null)

const latestPrediction = computed(() =>
  predictions.value.find(p => p.region === selectedRegion.value) ?? null
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

onMounted(async () => {
  models.value = await getModels()
  await loadRegionData()
})

watch(selectedRegion, loadRegionData)

async function runPrediction() {
  predicting.value = true
  try {
    const result = await apiRunPrediction(selectedRegion.value)
    // Prepend so it shows as latest
    predictions.value = [result, ...predictions.value.filter(p => p.region !== selectedRegion.value)]
  } catch (e: any) {
    alert('Prediction failed: ' + e.message)
  } finally {
    predicting.value = false
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
