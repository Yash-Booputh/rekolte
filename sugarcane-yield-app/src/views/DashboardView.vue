<template>
  <ion-page>
    <div class="flex flex-col h-screen bg-parchment leaf-pattern text-slate-900">

      <!-- Top Navigation Bar -->
      <header class="flex items-center justify-between bg-primary text-white px-8 py-4 shadow-lg sticky top-0 z-50">
        <div class="flex items-center gap-3">
          <div class="bg-accent p-1.5 rounded-lg">
            <span class="material-symbols-outlined text-white text-2xl">agriculture</span>
          </div>
          <h1 class="text-2xl font-black tracking-tight uppercase">Rékolte</h1>
        </div>

        <nav class="hidden md:flex items-center gap-10">
          <router-link to="/dashboard" class="text-sm font-bold border-b-2 border-accent pb-1">Dashboard</router-link>
          <router-link to="/regions"   class="text-sm font-medium text-white/80 hover:text-white transition-colors">Regions</router-link>
          <router-link to="/history"   class="text-sm font-medium text-white/80 hover:text-white transition-colors">History</router-link>
          <router-link to="/compare"   class="text-sm font-medium text-white/80 hover:text-white transition-colors">Compare</router-link>
        </nav>

        <div class="flex items-center gap-4">
          <button class="p-2 hover:bg-white/10 rounded-full transition-colors relative">
            <span class="material-symbols-outlined">notifications</span>
            <span class="absolute top-2 right-2 size-2 bg-accent rounded-full border-2 border-primary"></span>
          </button>
          <div class="h-8 w-px bg-white/20 mx-2"></div>
          <div class="flex items-center gap-3 cursor-pointer">
            <div class="text-right hidden sm:block">
              <p class="text-xs font-bold">Jean Pierre</p>
              <p class="text-[10px] text-white/60">Agronomist</p>
            </div>
            <div class="size-10 rounded-full border-2 border-accent bg-white/20 flex items-center justify-center">
              <span class="material-symbols-outlined text-sm">person</span>
            </div>
          </div>
        </div>
      </header>

      <!-- Main Content -->
      <main class="flex-1 flex overflow-hidden">

        <!-- Left: Map -->
        <section class="flex-1 relative p-6 flex flex-col gap-4">
          <div class="flex items-center justify-between mb-2">
            <div>
              <h2 class="text-xl font-bold text-primary flex items-center gap-2">
                <span class="material-symbols-outlined">map</span>
                Mauritius Regional Yield Map
              </h2>
              <p class="text-sm text-slate-600">Spatial distribution of predicted sugarcane tonnage</p>
            </div>
            <div class="flex bg-white p-1 rounded-lg shadow-sm border border-slate-200">
              <button
                :class="mapMode === 'heatmap' ? 'bg-primary text-white' : 'text-slate-500 hover:text-primary'"
                class="px-4 py-1.5 text-xs font-bold rounded-md transition-colors"
                @click="mapMode = 'heatmap'"
              >Heatmap</button>
              <button
                :class="mapMode === 'satellite' ? 'bg-primary text-white' : 'text-slate-500 hover:text-primary'"
                class="px-4 py-1.5 text-xs font-bold rounded-md transition-colors"
                @click="mapMode = 'satellite'"
              >Satellite</button>
            </div>
          </div>

          <!-- Leaflet choropleth map — explicit height so Leaflet can measure the container -->
          <div class="flex-1 rounded-xl border border-slate-200 shadow-inner relative" style="min-height:420px; position:relative;">
            <LeafletMap
              :region-values="mapRegionValues"
              :selected-region="selectedMapRegion"
              :mode="mapMode"
              @region-click="onRegionClick"
            />

            <!-- Legend overlay -->
            <div class="absolute bottom-4 left-4 z-[1000] bg-white/90 backdrop-blur p-4 rounded-lg shadow-md border border-slate-200 pointer-events-none">
              <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3">Yield (TCH)</p>
              <div class="flex flex-col gap-2">
                <div class="flex items-center gap-2">
                  <div class="size-3 rounded-sm" style="background:#2d5016"></div>
                  <span class="text-xs text-slate-700 font-medium">High (&gt;80)</span>
                </div>
                <div class="flex items-center gap-2">
                  <div class="size-3 rounded-sm" style="background:#4a8524"></div>
                  <span class="text-xs text-slate-700 font-medium">Optimal (70–80)</span>
                </div>
                <div class="flex items-center gap-2">
                  <div class="size-3 rounded-sm" style="background:#C8891A"></div>
                  <span class="text-xs text-slate-700 font-medium">Low (60–70)</span>
                </div>
                <div class="flex items-center gap-2">
                  <div class="size-3 rounded-sm" style="background:#dc2626"></div>
                  <span class="text-xs text-slate-700 font-medium">Very Low (&lt;60)</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Right: Summary Panel -->
        <aside class="w-[420px] bg-white/50 backdrop-blur-xl border-l border-slate-200 flex flex-col overflow-y-auto">
          <div class="p-8">
            <div class="mb-8">
              <span class="inline-block px-3 py-1 bg-accent/20 text-accent text-xs font-bold rounded-full mb-3 uppercase tracking-wider">Forecast Active</span>
              <h2 class="text-3xl font-black text-primary leading-tight">2025 Season Overview</h2>
              <p class="text-slate-500 mt-2 font-medium">National harvest predictions based on satellite NDVI data.</p>
            </div>

            <!-- Main Metric Card -->
            <div class="bg-primary rounded-xl p-6 text-white shadow-xl shadow-primary/20 mb-6 relative overflow-hidden group">
              <div class="absolute -right-4 -top-4 size-32 bg-white/5 rounded-full blur-2xl group-hover:bg-white/10 transition-colors"></div>
              <div class="flex items-start justify-between relative z-10">
                <div>
                  <p class="text-white/70 text-sm font-medium mb-1 uppercase tracking-wide">Avg. Predicted TCH</p>
                  <h3 class="text-5xl font-black text-accent">{{ nationalAvgTch }}</h3>
                </div>
                <div class="bg-white/10 p-2 rounded-lg">
                  <span class="material-symbols-outlined">trending_up</span>
                </div>
              </div>
              <div class="mt-4 flex items-center gap-2 relative z-10">
                <span class="text-emerald-400 font-bold flex items-center">
                  <span class="material-symbols-outlined text-sm">north</span> 3.8%
                </span>
                <span class="text-white/40 text-xs">vs. 2024 Season</span>
              </div>
            </div>

            <!-- Secondary Stats -->
            <div class="grid grid-cols-2 gap-4 mb-8">
              <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <p class="text-xs font-bold text-slate-400 uppercase tracking-tighter mb-1">Active Model</p>
                <p class="text-sm font-bold text-primary">XGBoost v1.0</p>
                <div class="mt-3 flex items-center gap-1.5">
                  <span class="size-2 bg-emerald-500 rounded-full animate-pulse"></span>
                  <span class="text-[10px] text-emerald-600 font-bold">Ready</span>
                </div>
              </div>
              <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <p class="text-xs font-bold text-slate-400 uppercase tracking-tighter mb-1">R² Score</p>
                <p class="text-sm font-bold text-primary">0.93</p>
                <div class="mt-3 w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                  <div class="bg-accent h-full w-[93%]"></div>
                </div>
              </div>
            </div>

            <!-- Regional Breakdown -->
            <div>
              <div class="flex items-center justify-between mb-4">
                <h4 class="font-bold text-primary text-sm uppercase tracking-wide">Regional Breakdown</h4>
                <router-link to="/regions" class="text-xs font-bold text-accent hover:underline">View All</router-link>
              </div>
              <div class="space-y-3">
                <div
                  v-for="row in season2025"
                  :key="row.region"
                  class="flex items-center justify-between p-3 bg-white rounded-lg border transition-all cursor-pointer group"
                  :class="row.tch < 70 ? 'border-accent/20 bg-accent/[0.03]' : 'border-slate-100 hover:border-accent/30'"
                  @click="$router.push('/regions')"
                >
                  <div class="flex items-center gap-3">
                    <div
                      class="size-8 rounded flex items-center justify-center font-bold text-xs transition-colors"
                      :class="row.tch < 70 ? 'bg-accent/20 text-accent group-hover:bg-accent group-hover:text-white' : 'bg-primary/10 text-primary group-hover:bg-accent group-hover:text-white'"
                    >
                      {{ regionMeta(row.region).abbr }}
                    </div>
                    <div>
                      <p class="text-sm font-bold text-slate-800">{{ regionMeta(row.region).label }}</p>
                      <p class="text-[10px] text-slate-400">{{ regionMeta(row.region).description }}</p>
                    </div>
                  </div>
                  <div class="text-right">
                    <p class="text-sm font-black" :class="row.tch < 70 ? 'text-accent' : 'text-primary'">{{ row.tch }}</p>
                    <p class="text-[10px] font-bold" :class="tchTrend(row.region) >= 0 ? 'text-emerald-500' : 'text-red-500'">
                      {{ tchTrend(row.region) >= 0 ? '+' : '' }}{{ tchTrend(row.region) }}%
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Export CTA -->
            <div class="mt-8 p-6 bg-parchment rounded-xl border-2 border-dashed border-primary/20 flex flex-col items-center text-center">
              <span class="material-symbols-outlined text-primary/40 text-4xl mb-2">analytics</span>
              <h5 class="text-sm font-bold text-primary">Need a detailed report?</h5>
              <p class="text-xs text-slate-500 mt-1 mb-4">Generate a full CSV analysis for the selected regions.</p>
              <button class="w-full bg-primary text-white py-3 rounded-lg font-bold text-sm hover:bg-primary/90 transition-all shadow-md">
                Export Prediction Data
              </button>
            </div>
          </div>

          <div class="mt-auto p-6 border-t border-slate-100 text-center">
            <p class="text-[10px] text-slate-400 font-medium uppercase tracking-widest">© 2025 Rékolte · Middlesex University Mauritius</p>
          </div>
        </aside>
      </main>
    </div>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { IonPage } from '@ionic/vue'
import LeafletMap from '@/components/LeafletMap.vue'
import {
  regions,
  historicalData,
  getLatestSeasonData,
  type Region,
} from '@/data/mockData'

const mapMode = ref<'heatmap' | 'satellite'>('heatmap')
const selectedMapRegion = ref<Region | null>(null)

const season2025 = computed(() => getLatestSeasonData(2025))

const nationalAvgTch = computed(() => {
  const vals = season2025.value.map(d => d.tch)
  return (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1)
})

// Values passed to Leaflet choropleth
const mapRegionValues = computed(() =>
  season2025.value.map(d => ({ region: d.region, tch: d.tch }))
)

function onRegionClick(region: Region) {
  selectedMapRegion.value = selectedMapRegion.value === region ? null : region
}

function regionMeta(id: Region) {
  return regions.find(r => r.id === id)!
}

function tchTrend(region: Region): number {
  const r2025 = historicalData.find(d => d.season === 2025 && d.region === region)
  const r2024 = historicalData.find(d => d.season === 2024 && d.region === region)
  if (!r2025 || !r2024) return 0
  return parseFloat((((r2025.tch - r2024.tch) / r2024.tch) * 100).toFixed(1))
}
</script>
