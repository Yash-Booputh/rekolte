<template>
  <ion-page>
    <div class="min-h-screen bg-background-light text-slate-900 font-sans">

      <!-- Navigation -->
      <header class="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-primary/10">
        <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div class="flex items-center gap-8">
            <div class="flex items-center gap-3 text-primary">
              <span class="material-symbols-outlined text-3xl font-bold">agriculture</span>
              <h2 class="text-xl font-bold tracking-tight">Rékolte</h2>
            </div>
            <nav class="hidden md:flex items-center gap-6">
              <router-link to="/dashboard" class="text-sm font-semibold text-primary/70 hover:text-primary transition-colors">Dashboard</router-link>
              <router-link to="/regions"   class="text-sm font-semibold text-primary border-b-2 border-primary pb-1">Regions</router-link>
              <router-link to="/history"   class="text-sm font-semibold text-primary/70 hover:text-primary transition-colors">History</router-link>
              <router-link to="/compare"   class="text-sm font-semibold text-primary/70 hover:text-primary transition-colors">Compare</router-link>
            </nav>
          </div>
          <div class="flex items-center gap-4">
            <button class="p-2 rounded-full hover:bg-primary/5 transition-colors">
              <span class="material-symbols-outlined text-primary">notifications</span>
            </button>
            <div class="size-9 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center">
              <span class="material-symbols-outlined text-primary text-sm">person</span>
            </div>
          </div>
        </div>
      </header>

      <main class="max-w-7xl mx-auto px-6 py-8">

        <!-- Header -->
        <div class="mb-8">
          <nav class="flex items-center gap-2 text-sm text-primary/60 mb-4 font-medium">
            <router-link to="/dashboard" class="hover:text-primary">Dashboard</router-link>
            <span class="material-symbols-outlined text-xs">chevron_right</span>
            <span class="text-primary font-bold">Region Detail</span>
          </nav>
          <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <!-- Region Selector -->
              <div class="flex items-center gap-3 mb-2">
                <h1 class="text-5xl font-black text-primary tracking-tight">{{ selectedRegionMeta.label }} Region</h1>
                <select
                  v-model="selectedRegion"
                  class="ml-4 border border-primary/20 rounded-lg px-3 py-1.5 text-sm font-semibold text-primary bg-white focus:ring-2 focus:ring-primary/20"
                >
                  <option v-for="r in regions" :key="r.id" :value="r.id">{{ r.label }}</option>
                </select>
              </div>
              <p class="text-primary/60 text-lg">Real-time Agricultural Performance &amp; Predictive Intelligence</p>
            </div>
            <div class="flex gap-3">
              <button class="flex items-center gap-2 px-5 py-2.5 rounded-lg border border-primary/20 text-primary font-semibold hover:bg-primary/5 transition-all">
                <span class="material-symbols-outlined text-xl">file_download</span>
                Export Dataset
              </button>
              <button class="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-white font-semibold shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all">
                <span class="material-symbols-outlined text-xl">refresh</span>
                Run Simulation
              </button>
            </div>
          </div>
        </div>

        <!-- Main Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">

          <!-- Yield Forecast Card -->
          <div class="lg:col-span-5 flex flex-col gap-6">
            <div class="bg-white rounded-xl p-8 border border-primary/10 shadow-sm relative overflow-hidden group">
              <div class="absolute top-0 right-0 p-4">
                <span class="material-symbols-outlined text-primary/10 text-6xl rotate-12 group-hover:rotate-0 transition-transform duration-500">analytics</span>
              </div>
              <h3 class="text-primary/70 font-bold uppercase tracking-wider text-xs mb-6">Yield Forecasting (TCH)</h3>

              <!-- Model Toggle -->
              <div class="bg-primary/5 p-1 rounded-xl flex items-center mb-10">
                <button
                  @click="activeModel = 'RandomForest'"
                  :class="activeModel === 'RandomForest' ? 'bg-primary text-white shadow-sm' : 'text-primary/60 hover:text-primary'"
                  class="flex-1 py-2 px-4 rounded-lg font-bold text-sm transition-all"
                >Random Forest</button>
                <button
                  @click="activeModel = 'XGBoost'"
                  :class="activeModel === 'XGBoost' ? 'bg-primary text-white shadow-sm' : 'text-primary/60 hover:text-primary'"
                  class="flex-1 py-2 px-4 rounded-lg font-bold text-sm transition-all"
                >XGBoost</button>
              </div>

              <div class="space-y-8">
                <div>
                  <p class="text-sm font-medium text-primary/50 mb-1">Predicted TCH (2025)</p>
                  <div class="flex items-baseline gap-3">
                    <span class="text-6xl font-black text-primary">{{ predictedTch }}</span>
                    <span class="text-xl font-bold text-accent-gold">tons/ha</span>
                  </div>
                </div>
                <div class="flex items-center gap-8 py-6 border-y border-primary/5">
                  <div>
                    <p class="text-xs font-bold text-primary/40 uppercase mb-1">Actual (2025)</p>
                    <p class="text-2xl font-bold text-slate-700">{{ actualTch }}</p>
                  </div>
                  <div class="w-px h-10 bg-primary/10"></div>
                  <div>
                    <p class="text-xs font-bold text-primary/40 uppercase mb-1">Variance</p>
                    <div class="flex items-center gap-1 font-bold text-xl" :class="variance >= 0 ? 'text-green-600' : 'text-red-500'">
                      <span class="material-symbols-outlined">{{ variance >= 0 ? 'trending_up' : 'trending_down' }}</span>
                      <span>{{ Math.abs(variance) }}%</span>
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-3 p-4 bg-accent-gold/10 rounded-lg border border-accent-gold/20">
                  <span class="material-symbols-outlined text-accent-gold font-bold">verified_user</span>
                  <p class="text-sm text-primary/80 leading-snug">
                    <span class="font-bold">Model R²: {{ activeModelMetrics?.r2 }}</span><br/>
                    RMSE: {{ activeModelMetrics?.rmse }} · MAE: {{ activeModelMetrics?.mae }}
                  </p>
                </div>
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
                <div class="flex items-center gap-4 text-xs font-bold">
                  <div class="flex items-center gap-1.5">
                    <span class="size-2 rounded-full bg-primary"></span><span>ACTUAL</span>
                  </div>
                </div>
              </div>
              <Line :data="chartData" :options="chartOptions" class="max-h-64" />
              <div class="mt-8 grid grid-cols-2 gap-4">
                <div class="p-4 rounded-lg bg-background-light border border-primary/5">
                  <p class="text-xs font-bold text-primary/40 uppercase mb-1">Peak Performance</p>
                  <p class="text-lg font-bold text-primary">
                    {{ peakSeason.tch }} <span class="text-sm font-normal">TCH ({{ peakSeason.season }})</span>
                  </p>
                </div>
                <div class="p-4 rounded-lg bg-background-light border border-primary/5">
                  <p class="text-xs font-bold text-primary/40 uppercase mb-1">18-Season Avg</p>
                  <p class="text-lg font-bold text-primary">
                    {{ seasonAvg }} <span class="text-sm font-normal">TCH</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Key Stats Row -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="bg-white rounded-xl p-6 border-b-4 border-primary shadow-sm hover:shadow-md transition-all group">
            <div class="flex items-center gap-4 mb-4">
              <div class="size-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                <span class="material-symbols-outlined">map</span>
              </div>
              <div>
                <h4 class="text-xs font-bold text-primary/50 uppercase tracking-widest">Surface Harvested</h4>
                <p class="text-2xl font-black text-primary">{{ latestRow?.surface_harvested.toLocaleString() }} <span class="text-sm font-bold opacity-60">Ha</span></p>
              </div>
            </div>
          </div>
          <div class="bg-white rounded-xl p-6 border-b-4 border-accent-gold shadow-sm hover:shadow-md transition-all group">
            <div class="flex items-center gap-4 mb-4">
              <div class="size-12 rounded-lg bg-accent-gold/10 flex items-center justify-center text-accent-gold group-hover:bg-accent-gold group-hover:text-white transition-colors">
                <span class="material-symbols-outlined">factory</span>
              </div>
              <div>
                <h4 class="text-xs font-bold text-primary/50 uppercase tracking-widest">Cane Production</h4>
                <p class="text-2xl font-black text-primary">{{ (latestRow ? (latestRow.cane_production / 1000).toFixed(0) : '–') }}K <span class="text-sm font-bold opacity-60">Tons</span></p>
              </div>
            </div>
          </div>
          <div class="bg-white rounded-xl p-6 border-b-4 border-primary/40 shadow-sm hover:shadow-md transition-all group">
            <div class="flex items-center gap-4 mb-4">
              <div class="size-12 rounded-lg bg-primary/5 flex items-center justify-center text-primary/60 group-hover:bg-primary/20 transition-colors">
                <span class="material-symbols-outlined">science</span>
              </div>
              <div>
                <h4 class="text-xs font-bold text-primary/50 uppercase tracking-widest">Extraction Rate</h4>
                <p class="text-2xl font-black text-primary">{{ latestRow?.extraction_rate ?? '–' }} <span class="text-sm font-bold opacity-60">%</span></p>
              </div>
            </div>
          </div>
        </div>

        <footer class="mt-12 pt-8 border-t border-primary/10 flex justify-between items-center opacity-60">
          <p class="text-xs font-medium">Data: Mauritius Chamber of Agriculture Harvest Bulletins 2008–2025</p>
          <div class="flex gap-6 text-xs font-bold uppercase tracking-widest">
            <router-link to="/history" class="hover:text-primary transition-colors">Full History</router-link>
            <router-link to="/compare" class="hover:text-primary transition-colors">Compare Models</router-link>
          </div>
        </footer>
      </main>
    </div>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { IonPage } from '@ionic/vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler,
} from 'chart.js'
import {
  regions,
  historicalData,
  modelMetrics,
  currentSeasonPredictions,
  getTchHistory,
  type Region,
} from '@/data/mockData'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const selectedRegion = ref<Region>('CENTRE')
const activeModel = ref<'RandomForest' | 'XGBoost'>('XGBoost')

const selectedRegionMeta = computed(() => regions.find(r => r.id === selectedRegion.value)!)

const history = computed(() => getTchHistory(selectedRegion.value))

const latestRow = computed(() =>
  historicalData.find(d => d.season === 2025 && d.region === selectedRegion.value)
)

const prediction = computed(() =>
  currentSeasonPredictions.find(p => p.region === selectedRegion.value)
)

const predictedTch = computed(() => prediction.value?.predicted_tch.toFixed(1) ?? '–')
const actualTch    = computed(() => prediction.value?.actual_tch.toFixed(1) ?? '–')

const variance = computed(() => {
  if (!prediction.value) return 0
  return parseFloat((((prediction.value.predicted_tch - prediction.value.actual_tch) / prediction.value.actual_tch) * 100).toFixed(1))
})

const activeModelMetrics = computed(() =>
  modelMetrics.find(m => m.name === activeModel.value)
)

const peakSeason = computed(() => {
  const sorted = [...history.value].sort((a, b) => b.tch - a.tch)
  return sorted[0] ?? { tch: 0, season: '–' }
})

const seasonAvg = computed(() => {
  const vals = history.value.map(h => h.tch)
  return (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1)
})

const chartData = computed(() => ({
  labels: history.value.map(h => h.season.toString()),
  datasets: [
    {
      label: 'TCH',
      data: history.value.map(h => h.tch),
      borderColor: '#2d5016',
      backgroundColor: 'rgba(45, 80, 22, 0.08)',
      borderWidth: 2.5,
      pointBackgroundColor: '#d4af37',
      pointBorderColor: '#ffffff',
      pointBorderWidth: 2,
      pointRadius: 4,
      tension: 0.35,
      fill: true,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#2d5016',
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
      callbacks: {
        label: (ctx: any) => ` ${ctx.parsed.y} TCH`,
      },
    },
  },
  scales: {
    x: { grid: { display: false }, ticks: { font: { family: 'Work Sans', size: 10 }, color: '#94a3b8' } },
    y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { font: { family: 'Work Sans', size: 10 }, color: '#94a3b8' } },
  },
}
</script>
