<template>
  <ion-page>
    <div class="min-h-screen bg-background-light text-slate-900 font-sans flex">

      <!-- Sidebar -->
      <aside class="w-72 bg-white border-r border-border-muted flex flex-col h-screen sticky top-0 overflow-y-auto">
        <div class="p-6 flex flex-col gap-8">
          <!-- Brand -->
          <div class="flex items-center gap-3">
            <div class="bg-primary rounded-lg p-2 text-white">
              <span class="material-symbols-outlined text-2xl">potted_plant</span>
            </div>
            <div class="flex flex-col">
              <h1 class="text-primary text-xl font-black leading-none uppercase tracking-tighter">Rékolte</h1>
              <p class="text-sage text-xs font-medium uppercase tracking-widest">Agricultural Analytics</p>
            </div>
          </div>

          <!-- Nav -->
          <nav class="flex flex-col gap-1">
            <router-link to="/dashboard" class="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-primary/10 hover:text-primary transition-colors">
              <span class="material-symbols-outlined">dashboard</span>
              <span class="text-sm font-semibold">Dashboard</span>
            </router-link>
            <router-link to="/history" class="flex items-center gap-3 px-3 py-2 rounded-lg bg-primary/10 text-primary">
              <span class="material-symbols-outlined">history</span>
              <span class="text-sm font-semibold">Historical Data</span>
            </router-link>
            <router-link to="/regions" class="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-primary/10 hover:text-primary transition-colors">
              <span class="material-symbols-outlined">map</span>
              <span class="text-sm font-semibold">Regions</span>
            </router-link>
            <router-link to="/compare" class="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-primary/10 hover:text-primary transition-colors">
              <span class="material-symbols-outlined">compare_arrows</span>
              <span class="text-sm font-semibold">Compare Models</span>
            </router-link>
          </nav>

          <div class="h-px bg-border-muted"></div>

          <!-- Filters -->
          <div class="flex flex-col gap-5">
            <h3 class="text-xs font-bold text-slate-400 uppercase tracking-widest">Filters</h3>
            <div class="flex flex-col gap-2">
              <label class="text-sm font-semibold text-slate-700">Region</label>
              <select v-model="filterRegion" class="w-full rounded-lg border-border-muted bg-parchment text-sm focus:ring-primary focus:border-primary">
                <option value="">All Regions</option>
                <option v-for="r in regions" :key="r.id" :value="r.id">{{ r.label }}</option>
              </select>
            </div>
            <div class="flex flex-col gap-2">
              <label class="text-sm font-semibold text-slate-700">Season Year</label>
              <select v-model="filterSeason" class="w-full rounded-lg border-border-muted bg-parchment text-sm focus:ring-primary focus:border-primary">
                <option value="">All Seasons</option>
                <option v-for="s in seasons" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
            <button @click="applyFilters" class="w-full bg-primary text-white py-2 rounded-lg text-sm font-bold shadow-sm hover:bg-primary/90 transition-all flex items-center justify-center gap-2">
              <span class="material-symbols-outlined text-sm">filter_list</span>
              Apply Filters
            </button>
            <button @click="clearFilters" class="w-full border border-border-muted text-slate-500 py-2 rounded-lg text-sm font-medium hover:bg-slate-50 transition-all">
              Clear
            </button>
          </div>
        </div>
        <div class="mt-auto p-6 flex flex-col gap-2">
          <a class="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-500 hover:text-primary transition-colors" href="#">
            <span class="material-symbols-outlined text-lg">help</span>
            <span class="text-sm font-medium">Data Sources</span>
          </a>
        </div>
      </aside>

      <!-- Main -->
      <main class="flex-1 flex flex-col overflow-x-hidden">
        <!-- Header -->
        <header class="h-20 bg-white/80 backdrop-blur-md sticky top-0 z-10 border-b border-border-muted px-8 flex items-center justify-between">
          <div>
            <h2 class="text-xl font-bold text-slate-900">Historical Harvest Analysis</h2>
            <p class="text-xs text-sage font-medium">{{ filteredData.length }} records · Seasons 2008–2025</p>
          </div>
          <div class="flex items-center gap-4">
            <div class="relative">
              <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">search</span>
              <input
                v-model="searchQuery"
                class="pl-10 pr-4 py-2 bg-background-light border-none rounded-full text-sm w-64 focus:ring-2 focus:ring-primary/20"
                placeholder="Search records..."
                type="text"
              />
            </div>
            <button class="bg-white border border-border-muted text-slate-700 px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 hover:bg-slate-50 transition-colors">
              <span class="material-symbols-outlined text-sm">download</span>
              Export CSV
            </button>
          </div>
        </header>

        <div class="p-8 flex flex-col gap-8 max-w-7xl mx-auto w-full">

          <!-- Bar Chart -->
          <section class="bg-white rounded-xl border border-border-muted p-6 shadow-sm">
            <div class="flex justify-between items-center mb-6">
              <div>
                <h3 class="text-lg font-bold text-slate-900">Annual TCH by Region</h3>
                <p class="text-sm text-slate-500">Select a season to compare all 5 regions</p>
              </div>
              <select v-model="chartSeason" class="border border-border-muted rounded-lg px-3 py-1.5 text-sm font-semibold text-primary bg-white">
                <option v-for="s in seasons" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
            <Bar :data="barChartData" :options="barChartOptions" class="max-h-64" />
          </section>

          <!-- Data Table -->
          <section class="bg-white rounded-xl border border-border-muted overflow-hidden shadow-sm">
            <div class="px-6 py-5 border-b border-border-muted flex justify-between items-center bg-parchment/50">
              <h3 class="font-bold text-slate-900">Season-End Records</h3>
              <span class="text-xs font-medium text-slate-500">Showing {{ paginatedData.length }} of {{ filteredData.length }}</span>
            </div>
            <div class="overflow-x-auto custom-scrollbar">
              <table class="w-full text-left border-collapse">
                <thead>
                  <tr class="bg-slate-50 text-slate-500 uppercase text-[10px] font-black tracking-widest">
                    <th class="px-6 py-4 cursor-pointer hover:text-primary" @click="sort('season')">
                      Season <span class="material-symbols-outlined text-xs align-middle">{{ sortField === 'season' ? (sortDir === 'asc' ? 'arrow_upward' : 'arrow_downward') : 'unfold_more' }}</span>
                    </th>
                    <th class="px-6 py-4">Region</th>
                    <th class="px-6 py-4 cursor-pointer hover:text-primary" @click="sort('surface_harvested')">Surface (Ha)</th>
                    <th class="px-6 py-4">Cane (T)</th>
                    <th class="px-6 py-4">Sugar (T)</th>
                    <th class="px-6 py-4">Ext (%)</th>
                    <th class="px-6 py-4 cursor-pointer hover:text-primary" @click="sort('tch')">
                      TCH <span class="material-symbols-outlined text-xs align-middle">{{ sortField === 'tch' ? (sortDir === 'asc' ? 'arrow_upward' : 'arrow_downward') : 'unfold_more' }}</span>
                    </th>
                    <th class="px-6 py-4">TSH</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-border-muted">
                  <tr
                    v-for="row in paginatedData"
                    :key="`${row.season}-${row.region}`"
                    class="hover:bg-slate-50 transition-colors"
                  >
                    <td class="px-6 py-4 font-bold text-sm">{{ row.season }}</td>
                    <td class="px-6 py-4">
                      <div class="flex items-center gap-2">
                        <span class="size-2 rounded-full" :style="{ backgroundColor: regionColor(row.region) }"></span>
                        <span class="text-sm font-medium">{{ regionLabel(row.region) }}</span>
                      </div>
                    </td>
                    <td class="px-6 py-4 text-sm font-semibold">{{ row.surface_harvested.toLocaleString() }}</td>
                    <td class="px-6 py-4 text-sm font-semibold">{{ row.cane_production.toLocaleString() }}</td>
                    <td class="px-6 py-4 text-sm font-semibold">{{ row.sugar_production?.toLocaleString() ?? '—' }}</td>
                    <td class="px-6 py-4 text-sm font-bold text-primary">{{ row.extraction_rate ?? '—' }}</td>
                    <td class="px-6 py-4">
                      <span
                        class="text-sm font-bold px-2 py-0.5 rounded"
                        :class="row.tch >= 80 ? 'bg-primary/10 text-primary' : row.tch >= 70 ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'"
                      >{{ row.tch }}</span>
                    </td>
                    <td class="px-6 py-4 text-sm font-bold">{{ row.tsh ?? '—' }}</td>
                  </tr>
                </tbody>
                <tfoot class="bg-parchment/80 font-bold border-t border-border-muted">
                  <tr>
                    <td class="px-6 py-4 text-sm uppercase" colspan="6">Average (filtered)</td>
                    <td class="px-6 py-4 text-sm text-primary">{{ filteredAvgTch }}</td>
                    <td class="px-6 py-4 text-sm">{{ filteredAvgTsh }}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </section>
        </div>

        <!-- Pagination -->
        <footer class="p-8 pt-0 max-w-7xl mx-auto w-full flex items-center justify-between">
          <div class="flex items-center gap-2">
            <button
              class="p-2 rounded-lg border border-border-muted hover:bg-white transition-colors disabled:opacity-50"
              :disabled="currentPage === 1"
              @click="currentPage--"
            >
              <span class="material-symbols-outlined">chevron_left</span>
            </button>
            <div class="flex gap-1">
              <button
                v-for="p in totalPages"
                :key="p"
                @click="currentPage = p"
                class="w-8 h-8 rounded-lg text-xs font-bold transition-colors"
                :class="currentPage === p ? 'bg-primary text-white' : 'border border-border-muted hover:bg-white'"
              >{{ p }}</button>
            </div>
            <button
              class="p-2 rounded-lg border border-border-muted hover:bg-white transition-colors disabled:opacity-50"
              :disabled="currentPage === totalPages"
              @click="currentPage++"
            >
              <span class="material-symbols-outlined">chevron_right</span>
            </button>
          </div>
          <p class="text-xs text-sage font-medium italic">Source: Mauritius Chamber of Agriculture Harvest Bulletins</p>
        </footer>
      </main>
    </div>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { IonPage } from '@ionic/vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  BarElement, Title, Tooltip, Legend,
} from 'chart.js'
import { regions, historicalData, type Region, type HarvestRecord } from '@/data/mockData'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

// Filters
const filterRegion = ref<Region | ''>('')
const filterSeason = ref<number | ''>('')
const searchQuery  = ref('')
const chartSeason  = ref(2025)

// Sorting
const sortField = ref<keyof HarvestRecord>('season')
const sortDir   = ref<'asc' | 'desc'>('desc')

// Pagination
const currentPage = ref(1)
const PAGE_SIZE   = 15

const seasons = computed(() =>
  [...new Set(historicalData.map(d => d.season))].sort((a, b) => b - a)
)

function applyFilters() { currentPage.value = 1 }
function clearFilters() {
  filterRegion.value = ''
  filterSeason.value = ''
  searchQuery.value  = ''
  currentPage.value  = 1
}

function sort(field: keyof HarvestRecord) {
  if (sortField.value === field) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDir.value = 'desc'
  }
}

const filteredData = computed(() => {
  let data = [...historicalData]
  if (filterRegion.value) data = data.filter(d => d.region === filterRegion.value)
  if (filterSeason.value) data = data.filter(d => d.season === filterSeason.value)
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    data = data.filter(d => d.region.toLowerCase().includes(q) || d.season.toString().includes(q))
  }
  data.sort((a, b) => {
    const av = a[sortField.value] as number ?? 0
    const bv = b[sortField.value] as number ?? 0
    return sortDir.value === 'asc' ? av - bv : bv - av
  })
  return data
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredData.value.length / PAGE_SIZE)))

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredData.value.slice(start, start + PAGE_SIZE)
})

const filteredAvgTch = computed(() => {
  const vals = filteredData.value.map(d => d.tch)
  return vals.length ? (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1) : '—'
})

const filteredAvgTsh = computed(() => {
  const vals = filteredData.value.filter(d => d.tsh !== null).map(d => d.tsh as number)
  return vals.length ? (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1) : '—'
})

function regionLabel(id: Region) { return regions.find(r => r.id === id)?.label ?? id }
function regionColor(id: Region) { return regions.find(r => r.id === id)?.color ?? '#2d5016' }

// Bar chart for selected season
const barChartData = computed(() => {
  const rows = historicalData.filter(d => d.season === chartSeason.value)
  return {
    labels: rows.map(r => regionLabel(r.region)),
    datasets: [{
      label: 'TCH',
      data: rows.map(r => r.tch),
      backgroundColor: rows.map(r => regionColor(r.region) + 'cc'),
      borderColor: rows.map(r => regionColor(r.region)),
      borderWidth: 2,
      borderRadius: 6,
    }],
  }
})

const barChartOptions = {
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
    x: { grid: { display: false }, ticks: { font: { family: 'Work Sans' }, color: '#64748b' } },
    y: {
      grid: { color: 'rgba(0,0,0,0.05)' },
      ticks: { font: { family: 'Work Sans' }, color: '#64748b' },
      suggestedMin: 40,
    },
  },
}
</script>
