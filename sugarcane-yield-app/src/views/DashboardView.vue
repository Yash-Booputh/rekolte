<template>
  <ion-page>
    <div class="flex flex-col h-screen bg-parchment leaf-pattern text-slate-900">
      <NavBar />

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
              >Map</button>
              <button
                :class="mapMode === 'satellite' ? 'bg-primary text-white' : 'text-slate-500 hover:text-primary'"
                class="px-4 py-1.5 text-xs font-bold rounded-md transition-colors"
                @click="mapMode = 'satellite'"
              >Satellite</button>
            </div>
          </div>

          <div class="flex-1 rounded-xl border border-slate-200 shadow-inner relative" style="min-height:420px; position:relative;">
            <LeafletMap
              :region-values="mapRegionValues"
              :selected-region="selectedMapRegion"
              :mode="mapMode"
              @region-click="onRegionClick"
            />
            <div class="absolute bottom-4 left-4 z-[1000] bg-white/90 backdrop-blur p-4 rounded-lg shadow-md border border-slate-200 pointer-events-none">
              <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3">Regions</p>
              <div class="flex flex-col gap-2">
                <div class="flex items-center gap-2"><div class="size-3 rounded-sm" style="background:#ef4444"></div><span class="text-xs text-slate-700 font-medium">Nord</span></div>
                <div class="flex items-center gap-2"><div class="size-3 rounded-sm" style="background:#3b82f6"></div><span class="text-xs text-slate-700 font-medium">Centre</span></div>
                <div class="flex items-center gap-2"><div class="size-3 rounded-sm" style="background:#eab308"></div><span class="text-xs text-slate-700 font-medium">Est</span></div>
                <div class="flex items-center gap-2"><div class="size-3 rounded-sm" style="background:#22c55e"></div><span class="text-xs text-slate-700 font-medium">Sud</span></div>
                <div class="flex items-center gap-2"><div class="size-3 rounded-sm" style="background:#f97316"></div><span class="text-xs text-slate-700 font-medium">Ouest</span></div>
              </div>
            </div>
          </div>
        </section>

        <!-- Right: Summary Panel -->
        <aside class="w-[420px] bg-white/50 backdrop-blur-xl border-l border-slate-200 flex flex-col overflow-y-auto">
          <div class="p-8">
            <div class="mb-8">
              <span class="inline-block px-3 py-1 bg-accent/20 text-accent text-xs font-bold rounded-full mb-3 uppercase tracking-wider">
                {{ activeModel ? 'Forecast Active' : 'No Model Active' }}
              </span>
              <h2 class="text-3xl font-black text-primary leading-tight">{{ latestSeason }} Season Overview</h2>
              <p class="text-slate-500 mt-2 font-medium">National harvest predictions based on satellite NDVI data.</p>
            </div>

            <!-- Loading state -->
            <div v-if="loading" class="flex items-center justify-center py-12">
              <svg class="animate-spin h-8 w-8 text-primary" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
            </div>

            <template v-else>
              <!-- Main Metric Card -->
              <div class="bg-primary rounded-xl p-6 text-white shadow-xl shadow-primary/20 mb-6 relative overflow-hidden group">
                <div class="absolute -right-4 -top-4 size-32 bg-white/5 rounded-full blur-2xl"></div>
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
                  <span class="text-white/40 text-xs">{{ latestPerRegion.length }} regions predicted</span>
                </div>
              </div>

              <!-- Active Model Card -->
              <div class="grid grid-cols-2 gap-4 mb-8">
                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <p class="text-xs font-bold text-slate-400 uppercase tracking-tighter mb-1">Active Model</p>
                  <p class="text-sm font-bold text-primary">{{ activeModel?.type ?? '—' }}</p>
                  <div class="mt-3 flex items-center gap-1.5">
                    <span class="size-2 bg-emerald-500 rounded-full animate-pulse"></span>
                    <span class="text-[10px] text-emerald-600 font-bold">{{ activeModel ? 'Ready' : 'None' }}</span>
                  </div>
                </div>
                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <p class="text-xs font-bold text-slate-400 uppercase tracking-tighter mb-1">LOSO R² Score</p>
                  <p class="text-sm font-bold text-primary">{{ activeModel ? activeModel.loso_r2.toFixed(4) : '—' }}</p>
                  <div v-if="activeModel" class="mt-3 w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                    <div class="bg-accent h-full" :style="`width: ${activeModel.loso_r2 * 100}%`"></div>
                  </div>
                </div>
              </div>

              <!-- Regional Breakdown -->
              <div>
                <div class="flex items-center justify-between mb-4">
                  <h4 class="font-bold text-primary text-sm uppercase tracking-wide">Regional Breakdown</h4>
                  <router-link to="/regions" class="text-xs font-bold text-accent hover:underline">View All</router-link>
                </div>
                <div v-if="latestPerRegion.length === 0" class="text-sm text-slate-400 text-center py-6">
                  No predictions yet. Go to Regions to run predictions.
                </div>
                <div v-else class="space-y-3">
                  <div
                    v-for="p in latestPerRegion" :key="p.region"
                    class="flex items-center justify-between p-3 bg-white rounded-lg border border-slate-100 hover:border-slate-300 transition-all cursor-pointer"
                    @click="$router.push('/regions')"
                  >
                    <div class="flex items-center gap-3">
                      <div
                        class="size-8 rounded flex items-center justify-center font-bold text-xs text-white"
                        :style="{ background: REGION_COLORS[p.region] ?? '#888' }"
                      >{{ p.region.slice(0,2) }}</div>
                      <div>
                        <p class="text-sm font-bold text-slate-800">{{ regionLabel(p.region) }}</p>
                        <p class="text-[10px] text-slate-400">Season {{ p.season }}</p>
                      </div>
                    </div>
                    <div class="text-right">
                      <p class="text-sm font-black text-slate-800">{{ p.predicted_tch.toFixed(1) }}</p>
                      <p class="text-[10px] text-slate-400">TCH</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Export CTA -->
              <div class="mt-8 p-6 bg-parchment rounded-xl border-2 border-dashed border-primary/20 flex flex-col items-center text-center">
                <span class="material-symbols-outlined text-primary/40 text-4xl mb-2">analytics</span>
                <h5 class="text-sm font-bold text-primary">Need a detailed report?</h5>
                <p class="text-xs text-slate-500 mt-1 mb-4">Generate a full PDF analysis for the current season.</p>
                <button
                  class="w-full bg-primary text-white py-3 rounded-lg font-bold text-sm hover:bg-primary/90 transition-all shadow-md flex items-center justify-center gap-2 disabled:opacity-50"
                  :disabled="reportLoading"
                  @click="downloadReport"
                >
                  <svg v-if="reportLoading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                  </svg>
                  <span class="material-symbols-outlined text-sm" v-else>download</span>
                  {{ reportLoading ? 'Generating…' : 'Export Prediction Report' }}
                </button>
              </div>
            </template>
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
import { ref, computed, onMounted, watch } from 'vue'
import { IonPage, onIonViewWillEnter } from '@ionic/vue'
import { modelActivatedAt } from '@/stores/appState'
import NavBar from '@/components/NavBar.vue'
import LeafletMap from '@/components/LeafletMap.vue'
import { REGION_COLORS } from '@/utils/regionColors'
import { getPredictions, getModels, generateReport } from '@/services/api'
import type { PredictionRecord, ModelConfig } from '@/services/api'
import type { Region } from '@/data/mockData'

const mapMode = ref<'heatmap' | 'satellite'>('satellite')
const selectedMapRegion = ref<Region | null>(null)
const loading = ref(true)
const reportLoading = ref(false)
const predictions = ref<PredictionRecord[]>([])
const models = ref<ModelConfig[]>([])

const activeModel = computed(() => models.value.find(m => m.is_active) ?? null)
const latestSeason = computed(() => predictions.value[0]?.season ?? new Date().getFullYear())

// Latest prediction per region — filtered to the active model only
const latestPerRegion = computed(() => {
  const activeType = activeModel.value?.type
  const map = new Map<string, PredictionRecord>()
  for (const p of predictions.value) {
    if (activeType && p.model_used !== activeType) continue
    if (!map.has(p.region)) map.set(p.region, p)
  }
  return Array.from(map.values())
})

const nationalAvgTch = computed(() => {
  const vals = latestPerRegion.value.map(p => p.predicted_tch)
  if (!vals.length) return '—'
  return (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1)
})

const mapRegionValues = computed(() =>
  latestPerRegion.value.map(p => ({ region: p.region as Region, tch: p.predicted_tch, model: p.model_used }))
)

async function refresh() {
  loading.value = true
  try {
    const [preds, mods] = await Promise.all([getPredictions(), getModels()])
    predictions.value = preds
    models.value = mods
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
onIonViewWillEnter(refresh)
watch(modelActivatedAt, refresh)

function onRegionClick(region: string | null) {
  selectedMapRegion.value = (region && selectedMapRegion.value !== region ? region : null) as Region | null
}

function regionLabel(id: string) {
  const labels: Record<string, string> = {
    NORD: 'Nord', EST: 'Est', SUD: 'Sud', OUEST: 'Ouest', CENTRE: 'Centre',
  }
  return labels[id] ?? id
}

async function downloadReport() {
  const season = latestPerRegion.value[0]?.season ?? latestSeason.value
  if (!season) {
    alert('No predictions available to generate a report. Run predictions first.')
    return
  }
  reportLoading.value = true
  try {
    const blob = await generateReport({ season: season as number })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `rekolte_report_${season}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: any) {
    alert('Report generation failed: ' + e.message)
  } finally {
    reportLoading.value = false
  }
}
</script>
