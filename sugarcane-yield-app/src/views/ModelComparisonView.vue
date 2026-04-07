<template>
  <ion-page>
    <div class="min-h-screen bg-background-light text-slate-900 font-sans">

      <!-- Navigation -->
      <header class="flex items-center justify-between border-b border-primary/10 px-10 py-3 bg-white/80 backdrop-blur-md sticky top-0 z-50">
        <div class="flex items-center gap-8">
          <div class="flex items-center gap-4 text-primary">
            <div class="size-8 flex items-center justify-center bg-primary rounded-lg text-white">
              <span class="material-symbols-outlined">eco</span>
            </div>
            <h2 class="text-slate-900 font-bold text-lg tracking-tight">Rékolte</h2>
          </div>
          <nav class="hidden md:flex items-center gap-6">
            <router-link to="/dashboard" class="text-slate-600 hover:text-primary text-sm font-medium transition-colors">Dashboard</router-link>
            <router-link to="/regions"   class="text-slate-600 hover:text-primary text-sm font-medium transition-colors">Regions</router-link>
            <router-link to="/history"   class="text-slate-600 hover:text-primary text-sm font-medium transition-colors">History</router-link>
            <router-link to="/compare"   class="text-primary text-sm font-bold border-b-2 border-primary py-1">Compare</router-link>
          </nav>
        </div>
        <div class="flex gap-2">
          <button class="flex items-center justify-center rounded-xl size-10 bg-primary/5 text-primary hover:bg-primary/10 transition-colors">
            <span class="material-symbols-outlined">notifications</span>
          </button>
        </div>
      </header>

      <main class="max-w-[1200px] mx-auto w-full px-6 py-8">

        <!-- Page Header -->
        <div class="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10">
          <div class="space-y-2">
            <div class="flex items-center gap-2 text-primary font-semibold text-sm uppercase tracking-wider">
              <span class="material-symbols-outlined text-sm">compare_arrows</span>
              Model Performance Comparison
            </div>
            <h1 class="text-4xl font-black text-slate-900 tracking-tight">Random Forest vs. XGBoost</h1>
            <p class="text-slate-500 max-w-2xl text-lg">
              Evaluation of sugarcane TCH prediction models using Leave-One-Season-Out cross-validation (18 seasons × 5 regions).
            </p>
          </div>
          <div class="flex bg-white p-1 rounded-xl shadow-sm border border-primary/10">
            <button
              @click="evalSet = 'test'"
              :class="evalSet === 'test' ? 'bg-primary text-white' : 'text-slate-500 hover:bg-primary/5'"
              class="px-6 py-2 rounded-lg text-sm font-bold transition-colors"
            >LOSO CV</button>
            <button
              @click="evalSet = 'train'"
              :class="evalSet === 'train' ? 'bg-primary text-white' : 'text-slate-500 hover:bg-primary/5'"
              class="px-6 py-2 rounded-lg text-sm font-bold transition-colors"
            >Train Set</button>
          </div>
        </div>

        <!-- Metric Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">

          <!-- RMSE -->
          <div class="bg-white rounded-xl p-6 shadow-sm border border-primary/10 relative overflow-hidden">
            <div class="absolute top-0 right-0 p-4 opacity-10">
              <span class="material-symbols-outlined text-4xl">analytics</span>
            </div>
            <h3 class="text-slate-500 font-semibold text-sm mb-4">RMSE <span class="text-xs text-slate-400">(lower is better)</span></h3>
            <div class="flex items-center justify-between">
              <div class="space-y-1">
                <p class="text-xs text-slate-400 uppercase font-bold">Random Forest</p>
                <p class="text-2xl font-bold text-slate-600">{{ rfMetrics.rmse }}</p>
              </div>
              <div class="h-10 w-px bg-primary/10"></div>
              <div class="space-y-1 text-right">
                <p class="text-xs text-primary uppercase font-bold">XGBoost</p>
                <p class="text-3xl font-black text-primary">{{ xgbMetrics.rmse }}</p>
              </div>
            </div>
            <div class="mt-4 flex items-center gap-2 bg-primary/10 text-primary px-3 py-1.5 rounded-lg w-fit">
              <span class="material-symbols-outlined text-sm font-bold">verified</span>
              <span class="text-xs font-bold uppercase tracking-tight">XGBoost {{ rmseWinPct }}% better</span>
            </div>
          </div>

          <!-- MAE -->
          <div class="bg-white rounded-xl p-6 shadow-sm border border-primary/10 relative overflow-hidden">
            <div class="absolute top-0 right-0 p-4 opacity-10">
              <span class="material-symbols-outlined text-4xl">straighten</span>
            </div>
            <h3 class="text-slate-500 font-semibold text-sm mb-4">MAE <span class="text-xs text-slate-400">(lower is better)</span></h3>
            <div class="flex items-center justify-between">
              <div class="space-y-1">
                <p class="text-xs text-slate-400 uppercase font-bold">Random Forest</p>
                <p class="text-2xl font-bold text-slate-600">{{ rfMetrics.mae }}</p>
              </div>
              <div class="h-10 w-px bg-primary/10"></div>
              <div class="space-y-1 text-right">
                <p class="text-xs text-primary uppercase font-bold">XGBoost</p>
                <p class="text-3xl font-black text-primary">{{ xgbMetrics.mae }}</p>
              </div>
            </div>
            <div class="mt-4 flex items-center gap-2 bg-primary/10 text-primary px-3 py-1.5 rounded-lg w-fit">
              <span class="material-symbols-outlined text-sm font-bold">verified</span>
              <span class="text-xs font-bold uppercase tracking-tight">XGBoost {{ maeWinPct }}% better</span>
            </div>
          </div>

          <!-- R² -->
          <div class="bg-white rounded-xl p-6 shadow-sm border border-primary/10 relative overflow-hidden">
            <div class="absolute top-0 right-0 p-4 opacity-10">
              <span class="material-symbols-outlined text-4xl">legend_toggle</span>
            </div>
            <h3 class="text-slate-500 font-semibold text-sm mb-4">R² Score <span class="text-xs text-slate-400">(higher is better)</span></h3>
            <div class="flex items-center justify-between">
              <div class="space-y-1">
                <p class="text-xs text-slate-400 uppercase font-bold">Random Forest</p>
                <p class="text-2xl font-bold text-slate-600">{{ rfMetrics.r2 }}</p>
              </div>
              <div class="h-10 w-px bg-primary/10"></div>
              <div class="space-y-1 text-right">
                <p class="text-xs text-primary uppercase font-bold">XGBoost</p>
                <p class="text-3xl font-black text-primary">{{ xgbMetrics.r2 }}</p>
              </div>
            </div>
            <div class="mt-4 flex items-center gap-2 bg-primary/10 text-primary px-3 py-1.5 rounded-lg w-fit">
              <span class="material-symbols-outlined text-sm font-bold">verified</span>
              <span class="text-xs font-bold uppercase tracking-tight">XGBoost {{ r2WinPct }}% better</span>
            </div>
          </div>
        </div>

        <!-- Scatter Plot: Predicted vs Actual -->
        <div class="bg-white rounded-xl p-8 shadow-sm border border-primary/10 mb-10">
          <div class="flex items-center justify-between mb-8">
            <div>
              <h2 class="text-xl font-bold text-slate-900">Predicted vs. Actual TCH</h2>
              <p class="text-slate-500 text-sm">Each point = one region-season prediction · Diagonal = perfect prediction</p>
            </div>
            <div class="flex items-center gap-6">
              <div class="flex items-center gap-2">
                <span class="size-3 rounded-full bg-slate-300"></span>
                <span class="text-sm font-medium text-slate-600">Random Forest</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="size-3 rounded-full bg-primary"></span>
                <span class="text-sm font-medium text-slate-600">XGBoost</span>
              </div>
            </div>
          </div>
          <Scatter :data="scatterData" :options="scatterOptions" class="max-h-96" />
        </div>

        <!-- Feature Importance -->
        <div class="bg-white rounded-xl p-8 shadow-sm border border-primary/10">
          <div class="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
            <div>
              <h2 class="text-xl font-bold text-slate-900">Feature Importance Comparison</h2>
              <p class="text-slate-500 text-sm">Relative contribution of NDVI features and seasonal variables</p>
            </div>
          </div>
          <div class="space-y-6">
            <div v-for="feat in mergedFeatures" :key="feat.feature" class="space-y-2">
              <div class="flex justify-between text-sm font-bold">
                <span class="text-slate-700">{{ feat.feature }}</span>
                <span class="text-primary">XGB: {{ feat.xgb }} · RF: {{ feat.rf }}</span>
              </div>
              <div class="h-3 w-full bg-slate-100 rounded-full overflow-hidden flex">
                <div class="h-full bg-primary rounded-l-full" :style="`width: ${feat.xgb * 100}%`"></div>
                <div class="h-full bg-slate-300/60" :style="`width: ${feat.rf * 100}%`"></div>
              </div>
            </div>
          </div>
          <div class="mt-8 pt-6 border-t border-slate-100 flex items-center justify-center gap-8">
            <div class="flex items-center gap-2">
              <div class="size-3 bg-primary rounded-sm"></div>
              <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">XGBoost Weight</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="size-3 bg-slate-300/60 rounded-sm"></div>
              <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Random Forest Importance</span>
            </div>
          </div>
        </div>
      </main>

      <footer class="mt-auto border-t border-primary/10 py-8 px-10 bg-white">
        <div class="max-w-[1200px] mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div class="flex items-center gap-2 text-primary/60">
            <span class="material-symbols-outlined text-sm">copyright</span>
            <span class="text-sm font-medium">2025 Rékolte · Middlesex University Mauritius</span>
          </div>
          <p class="text-xs text-slate-400">Metrics are placeholder values pending model training completion.</p>
        </div>
      </footer>
    </div>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { IonPage } from '@ionic/vue'
import { Scatter } from 'vue-chartjs'
import {
  Chart as ChartJS, LinearScale, PointElement,
  LineElement, Tooltip, Legend,
} from 'chart.js'
import { modelMetrics } from '@/data/mockData'

ChartJS.register(LinearScale, PointElement, LineElement, Tooltip, Legend)

const evalSet = ref<'test' | 'train'>('test')

const rfMetrics  = computed(() => modelMetrics.find(m => m.name === 'RandomForest')!)
const xgbMetrics = computed(() => modelMetrics.find(m => m.name === 'XGBoost')!)

const rmseWinPct = computed(() =>
  (((rfMetrics.value.rmse - xgbMetrics.value.rmse) / rfMetrics.value.rmse) * 100).toFixed(1)
)
const maeWinPct = computed(() =>
  (((rfMetrics.value.mae - xgbMetrics.value.mae) / rfMetrics.value.mae) * 100).toFixed(1)
)
const r2WinPct = computed(() =>
  (((xgbMetrics.value.r2 - rfMetrics.value.r2) / rfMetrics.value.r2) * 100).toFixed(1)
)

const scatterData = computed(() => ({
  datasets: [
    {
      label: 'Random Forest',
      data: rfMetrics.value.predictions.map(p => ({ x: p.actual, y: p.predicted })),
      backgroundColor: 'rgba(100,116,139,0.4)',
      pointRadius: 6,
      pointHoverRadius: 8,
    },
    {
      label: 'XGBoost',
      data: xgbMetrics.value.predictions.map(p => ({ x: p.actual, y: p.predicted })),
      backgroundColor: 'rgba(45,80,22,0.7)',
      pointRadius: 7,
      pointHoverRadius: 9,
      pointBorderColor: '#ffffff',
      pointBorderWidth: 1.5,
    },
  ],
}))

const scatterOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#2d5016',
      callbacks: {
        label: (ctx: any) => ` Actual: ${ctx.parsed.x} → Predicted: ${ctx.parsed.y}`,
      },
    },
  },
  scales: {
    x: {
      title: { display: true, text: 'Actual TCH', font: { family: 'Work Sans', weight: 'bold' as const }, color: '#94a3b8' },
      grid: { color: 'rgba(0,0,0,0.05)' },
      ticks: { font: { family: 'Work Sans' }, color: '#94a3b8' },
    },
    y: {
      title: { display: true, text: 'Predicted TCH', font: { family: 'Work Sans', weight: 'bold' as const }, color: '#94a3b8' },
      grid: { color: 'rgba(0,0,0,0.05)' },
      ticks: { font: { family: 'Work Sans' }, color: '#94a3b8' },
    },
  },
}

const mergedFeatures = computed(() =>
  xgbMetrics.value.featureImportance.map((xf, i) => ({
    feature: xf.feature,
    xgb: xf.importance,
    rf: rfMetrics.value.featureImportance[i]?.importance ?? 0,
  }))
)
</script>
