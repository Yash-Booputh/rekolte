<template>
  <ion-page>
    <div class="h-full overflow-y-auto bg-parchment text-slate-900 font-sans flex flex-col">
      <NavBar />

      <main class="px-6 py-8 w-full flex flex-col gap-8">

        <!-- Page Header -->
        <div>
          <h2 class="text-3xl font-black text-primary">Historical Harvest Analysis</h2>
          <p class="text-slate-500 text-sm mt-1">Seasons 2008–2025</p>
        </div>

        <!-- Bar Chart -->
        <section class="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div class="flex justify-between items-center mb-6">
            <div>
              <h3 class="text-lg font-bold text-slate-900">Annual TCH by Region</h3>
              <p class="text-sm text-slate-500">Compare all 5 regions for a selected season</p>
            </div>
            <select v-model="chartSeason" class="border border-slate-200 rounded-lg px-3 py-1.5 text-sm font-semibold text-primary bg-white outline-none">
              <option v-for="s in seasons" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div v-if="loading" class="flex items-center justify-center h-32">
            <svg class="animate-spin h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
          </div>
          <Bar v-else :data="barChartData" :options="barChartOptions" class="max-h-64" />
        </section>

        <!-- Bulletins Section -->
        <section class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-primary/5">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-primary">description</span>
              <h3 class="font-bold text-primary">Harvest Bulletins</h3>
              <span class="text-xs text-slate-400">({{ bulletins.length }} files)</span>
            </div>
            <div class="flex items-center gap-3">
              <select v-model="bulletinSeasonFilter" class="border border-slate-200 rounded-lg px-3 py-1.5 text-xs font-semibold text-primary bg-white outline-none">
                <option value="">All Seasons</option>
                <option v-for="s in seasons" :key="s" :value="s">{{ s }}</option>
              </select>
              <label class="flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-lg text-sm font-bold cursor-pointer hover:bg-primary/90 transition-colors">
                <span class="material-symbols-outlined text-sm">upload</span>
                Upload PDF
                <input type="file" accept=".pdf" class="hidden" @change="handleBulletinUpload" />
              </label>
            </div>
          </div>

          <!-- Upload form (shown after file selected) -->
          <div v-if="pendingFile" class="px-6 py-4 bg-parchment border-b border-slate-200 flex items-center gap-4 flex-wrap">
            <span class="text-sm font-medium text-slate-700">{{ pendingFile.name }}</span>
            <select v-model="uploadType" class="border border-slate-200 rounded-lg px-3 py-1.5 text-sm text-primary bg-white outline-none">
              <option value="weekly">Weekly Bulletin</option>
              <option value="crop_report">Crop Report</option>
              <option value="other">Other</option>
            </select>
            <input v-model="uploadSeason" type="number" placeholder="Season (year)" class="border border-slate-200 rounded-lg px-3 py-1.5 text-sm w-36 outline-none" />
            <input v-model="uploadWeek" type="number" placeholder="Week #" class="border border-slate-200 rounded-lg px-3 py-1.5 text-sm w-28 outline-none" />
            <button
              class="bg-primary text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2"
              :disabled="uploading"
              @click="confirmUpload"
            >
              <svg v-if="uploading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
              {{ uploading ? 'Uploading…' : 'Confirm Upload' }}
            </button>
            <button class="text-slate-400 hover:text-slate-600 text-sm" @click="pendingFile = null">Cancel</button>
          </div>

          <div v-if="bulletinLoading" class="flex items-center justify-center py-8">
            <svg class="animate-spin h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
          </div>
          <div v-else-if="filteredBulletins.length === 0" class="px-6 py-8 text-center text-slate-400 text-sm">
            No bulletins found. Upload a PDF to get started.
          </div>
          <div v-else class="divide-y divide-slate-100">
            <div
              v-for="b in paginatedBulletins" :key="b._id"
              class="flex items-center justify-between px-6 py-3 hover:bg-slate-50 transition-colors"
            >
              <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-primary/40">picture_as_pdf</span>
                <div>
                  <p class="text-sm font-semibold text-slate-800">{{ b.filename }}</p>
                  <p class="text-xs text-slate-400">
                    Season {{ b.season ?? '—' }}
                    <span v-if="b.week"> · Week {{ b.week }}</span>
                    · {{ b.type }}
                  </p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <a :href="b.preview_url" target="_blank" class="text-xs font-bold text-primary hover:underline flex items-center gap-1">
                  <span class="material-symbols-outlined text-sm">visibility</span> View
                </a>
                <a :href="b.download_url" target="_blank" class="text-xs font-bold text-accent hover:underline flex items-center gap-1">
                  <span class="material-symbols-outlined text-sm">download</span> Download
                </a>
                <button class="text-red-400 hover:text-red-600 ml-2" @click="deleteBulletin(b._id)">
                  <span class="material-symbols-outlined text-sm">delete</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Bulletin pagination -->
          <div v-if="bulletinTotalPages > 1" class="flex items-center justify-between px-6 py-3 border-t border-slate-100 bg-slate-50">
            <span class="text-xs text-slate-400">
              {{ (bulletinPage - 1) * BULLETIN_PAGE_SIZE + 1 }}–{{ Math.min(bulletinPage * BULLETIN_PAGE_SIZE, filteredBulletins.length) }}
              of {{ filteredBulletins.length }}
            </span>
            <div class="flex items-center gap-1">
              <button
                class="p-1.5 rounded border border-slate-200 hover:bg-white disabled:opacity-40"
                :disabled="bulletinPage === 1"
                @click="bulletinPage--"
              >
                <span class="material-symbols-outlined text-sm">chevron_left</span>
              </button>
              <template v-for="p in bulletinPageButtons" :key="p">
                <span v-if="p === '...'" class="w-7 h-7 flex items-center justify-center text-xs text-slate-400">…</span>
                <button
                  v-else
                  @click="bulletinPage = Number(p)"
                  class="w-7 h-7 rounded border text-xs font-bold transition-colors"
                  :class="bulletinPage === p ? 'bg-primary text-white border-primary' : 'border-slate-200 hover:bg-white'"
                >{{ p }}</button>
              </template>
              <button
                class="p-1.5 rounded border border-slate-200 hover:bg-white disabled:opacity-40"
                :disabled="bulletinPage === bulletinTotalPages"
                @click="bulletinPage++"
              >
                <span class="material-symbols-outlined text-sm">chevron_right</span>
              </button>
            </div>
          </div>
        </section>

        <!-- Data Table -->
        <section class="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
          <div class="px-6 py-4 border-b border-slate-100 bg-parchment/50 flex flex-wrap items-center gap-3">
            <h3 class="font-bold text-slate-900 mr-2">Season-End Records</h3>

            <!-- Region filter -->
            <select v-model="filterRegion" class="border border-slate-200 rounded-lg px-3 py-1.5 text-sm font-semibold text-primary bg-white focus:ring-primary focus:border-primary outline-none">
              <option value="">All Regions</option>
              <option v-for="r in REGIONS" :key="r" :value="r">{{ regionLabel(r) }}</option>
            </select>

            <!-- Season filter -->
            <select v-model="filterSeason" class="border border-slate-200 rounded-lg px-3 py-1.5 text-sm font-semibold text-primary bg-white focus:ring-primary focus:border-primary outline-none">
              <option value="">All Seasons</option>
              <option v-for="s in seasons" :key="s" :value="s">{{ s }}</option>
            </select>

            <!-- Search -->
            <div class="relative">
              <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-base">search</span>
              <input
                v-model="searchQuery"
                class="pl-9 pr-4 py-1.5 bg-white border border-slate-200 rounded-lg text-sm w-44 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                placeholder="Search…"
              />
            </div>

            <!-- Clear -->
            <button
              class="border border-slate-200 text-slate-600 px-3 py-1.5 rounded-lg text-sm font-bold flex items-center gap-1.5 hover:bg-white transition-colors"
              @click="clearFilters"
            >
              <span class="material-symbols-outlined text-sm">filter_list_off</span>
              Clear
            </button>

            <span class="ml-auto text-xs font-medium text-slate-500">{{ filteredData.length }} records</span>
          </div>
          <div v-if="loading" class="flex items-center justify-center py-12">
            <svg class="animate-spin h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
          </div>
          <div v-else class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-slate-50 text-slate-500 uppercase text-[10px] font-black tracking-widest">
                  <th class="px-6 py-4 cursor-pointer hover:text-primary" @click="sort('season')">
                    Season <span class="material-symbols-outlined text-xs align-middle">{{ sortIcon('season') }}</span>
                  </th>
                  <th class="px-6 py-4">Region</th>
                  <th class="px-6 py-4 cursor-pointer hover:text-primary" @click="sort('surface_harvested')">Surface (Ha)</th>
                  <th class="px-6 py-4">Cane (T)</th>
                  <th class="px-6 py-4">Sugar (T)</th>
                  <th class="px-6 py-4">Ext (%)</th>
                  <th class="px-6 py-4 cursor-pointer hover:text-primary" @click="sort('tch')">
                    TCH <span class="material-symbols-outlined text-xs align-middle">{{ sortIcon('tch') }}</span>
                  </th>
                  <th class="px-6 py-4">TSH</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-for="row in paginatedData" :key="`${row.season}-${row.region}`" class="hover:bg-slate-50 transition-colors">
                  <td class="px-6 py-4 font-bold text-sm">{{ row.season }}</td>
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-2">
                      <span class="size-2 rounded-full bg-primary"></span>
                      <span class="text-sm font-medium">{{ regionLabel(row.region) }}</span>
                    </div>
                  </td>
                  <td class="px-6 py-4 text-sm font-semibold">{{ row.surface_harvested?.toLocaleString() ?? '—' }}</td>
                  <td class="px-6 py-4 text-sm font-semibold">{{ row.cane_production?.toLocaleString() ?? '—' }}</td>
                  <td class="px-6 py-4 text-sm font-semibold">{{ row.sugar_production?.toLocaleString() ?? '—' }}</td>
                  <td class="px-6 py-4 text-sm font-bold text-primary">{{ row.extraction_rate ?? '—' }}</td>
                  <td class="px-6 py-4">
                    <span class="text-sm font-bold px-2 py-0.5 rounded"
                      :class="row.tch >= 80 ? 'bg-primary/10 text-primary' : row.tch >= 70 ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'">
                      {{ row.tch }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-sm font-bold">{{ row.tsh ?? '—' }}</td>
                </tr>
              </tbody>
              <tfoot class="bg-parchment/80 font-bold border-t border-slate-200">
                <tr>
                  <td class="px-6 py-4 text-sm uppercase" colspan="6">Average (filtered)</td>
                  <td class="px-6 py-4 text-sm text-primary">{{ filteredAvgTch }}</td>
                  <td class="px-6 py-4 text-sm">{{ filteredAvgTsh }}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </section>

        <!-- Pagination -->
        <div class="flex items-center justify-between pb-8">
          <div class="flex items-center gap-2">
            <button class="p-2 rounded-lg border border-slate-200 hover:bg-white disabled:opacity-50" :disabled="currentPage === 1" @click="currentPage--">
              <span class="material-symbols-outlined">chevron_left</span>
            </button>
            <div class="flex gap-1">
              <button
                v-for="p in totalPages" :key="p" @click="currentPage = p"
                class="w-8 h-8 rounded-lg text-xs font-bold transition-colors"
                :class="currentPage === p ? 'bg-primary text-white' : 'border border-slate-200 hover:bg-white'"
              >{{ p }}</button>
            </div>
            <button class="p-2 rounded-lg border border-slate-200 hover:bg-white disabled:opacity-50" :disabled="currentPage === totalPages" @click="currentPage++">
              <span class="material-symbols-outlined">chevron_right</span>
            </button>
          </div>
          <p class="text-xs text-slate-400 italic">Source: Mauritius Chamber of Agriculture Harvest Bulletins</p>
        </div>
      </main>
      <FooterBar />
    </div>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { IonPage } from '@ionic/vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'
import NavBar from '@/components/NavBar.vue'
import FooterBar from '@/components/FooterBar.vue'
import { getHarvest, getBulletins, uploadBulletin, deleteBulletin as apiDeleteBulletin } from '@/services/api'
import type { HarvestRecord, BulletinDoc } from '@/services/api'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const REGIONS = ['NORD', 'CENTRE', 'EST', 'SUD', 'OUEST']
const REGION_ORDER = ['NORD', 'CENTRE', 'EST', 'SUD', 'OUEST']
const REGION_COLORS: Record<string, string> = {
  NORD: '#ef4444',
  CENTRE: '#3b82f6',
  EST: '#eab308',
  SUD: '#22c55e',
  OUEST: '#f97316',
}

const loading = ref(true)
const bulletinLoading = ref(true)
const uploading = ref(false)
const allData = ref<HarvestRecord[]>([])
const bulletins = ref<BulletinDoc[]>([])

// Upload state
const pendingFile = ref<File | null>(null)
const uploadType = ref('weekly')
const uploadSeason = ref<number | ''>('')
const uploadWeek = ref<number | ''>('')

// Filters
const filterRegion = ref('')
const filterSeason = ref<number | ''>('')
const searchQuery = ref('')
const chartSeason = ref(2025)
const bulletinSeasonFilter = ref<number | ''>('')

// Sorting
const sortField = ref<keyof HarvestRecord>('season')
const sortDir = ref<'asc' | 'desc'>('desc')

// Harvest table pagination
const currentPage = ref(1)
const PAGE_SIZE = 15

// Bulletin pagination
const bulletinPage = ref(1)
const BULLETIN_PAGE_SIZE = 10

const seasons = computed(() =>
  [...new Set(allData.value.map(d => d.season))].sort((a, b) => b - a)
)

onMounted(async () => {
  const [harvest, buls] = await Promise.all([getHarvest(), getBulletins()])
  allData.value = harvest
  bulletins.value = buls
  if (seasons.value.length) chartSeason.value = seasons.value[0]
  loading.value = false
  bulletinLoading.value = false
})

function clearFilters() {
  filterRegion.value = ''
  filterSeason.value = ''
  searchQuery.value = ''
  currentPage.value = 1
}

function sort(field: keyof HarvestRecord) {
  if (sortField.value === field) sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  else { sortField.value = field; sortDir.value = 'desc' }
}
function sortIcon(field: string) {
  if (sortField.value !== field) return 'unfold_more'
  return sortDir.value === 'asc' ? 'arrow_upward' : 'arrow_downward'
}

const filteredData = computed(() => {
  currentPage.value = 1
  let data = [...allData.value]
  if (filterRegion.value) data = data.filter(d => d.region === filterRegion.value)
  if (filterSeason.value) data = data.filter(d => d.season === Number(filterSeason.value))
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    data = data.filter(d => d.region.toLowerCase().includes(q) || d.season.toString().includes(q))
  }
  data.sort((a, b) => {
    const av = (a[sortField.value] as number) ?? 0
    const bv = (b[sortField.value] as number) ?? 0
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

const filteredBulletins = computed(() => {
  bulletinPage.value = 1
  if (!bulletinSeasonFilter.value) return bulletins.value
  return bulletins.value.filter(b => b.season === bulletinSeasonFilter.value)
})

const bulletinTotalPages = computed(() =>
  Math.max(1, Math.ceil(filteredBulletins.value.length / BULLETIN_PAGE_SIZE))
)

const bulletinPageButtons = computed(() => {
  const total = bulletinTotalPages.value
  const cur = bulletinPage.value
  const pages: (number | string)[] = []

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
    return pages
  }

  pages.push(1)
  if (cur > 3) pages.push('...')
  for (let i = Math.max(2, cur - 1); i <= Math.min(total - 1, cur + 1); i++) pages.push(i)
  if (cur < total - 2) pages.push('...')
  pages.push(total)

  return pages
})

const paginatedBulletins = computed(() => {
  const start = (bulletinPage.value - 1) * BULLETIN_PAGE_SIZE
  return filteredBulletins.value.slice(start, start + BULLETIN_PAGE_SIZE)
})

function handleBulletinUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) pendingFile.value = file
}

async function confirmUpload() {
  if (!pendingFile.value) return
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', pendingFile.value)
    fd.append('type', uploadType.value)
    if (uploadSeason.value) fd.append('season', String(uploadSeason.value))
    if (uploadWeek.value) fd.append('week', String(uploadWeek.value))
    await uploadBulletin(fd)
    bulletins.value = await getBulletins()
    pendingFile.value = null
  } catch (e: any) {
    alert('Upload failed: ' + e.message)
  } finally {
    uploading.value = false
  }
}

async function deleteBulletin(id: string) {
  if (!confirm('Delete this bulletin?')) return
  await apiDeleteBulletin(id)
  bulletins.value = bulletins.value.filter(b => b._id !== id)
}

const barChartData = computed(() => {
  const byRegion = Object.fromEntries(
    allData.value.filter(d => d.season === chartSeason.value).map(r => [r.region, r.tch])
  )
  return {
    labels: REGION_ORDER.map(r => regionLabel(r)),
    datasets: [{
      label: 'TCH',
      data: REGION_ORDER.map(r => byRegion[r] ?? 0),
      backgroundColor: REGION_ORDER.map(r => REGION_COLORS[r] + 'cc'),
      borderColor: REGION_ORDER.map(r => REGION_COLORS[r]),
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
    tooltip: { backgroundColor: '#1e293b', callbacks: { label: (ctx: any) => ` ${ctx.parsed.y} TCH` } },
  },
  scales: {
    x: { grid: { display: false }, ticks: { color: '#64748b' } },
    y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#64748b' }, suggestedMin: 40 },
  },
}

function regionLabel(id: string) {
  const labels: Record<string, string> = { NORD: 'Nord', EST: 'Est', SUD: 'Sud', OUEST: 'Ouest', CENTRE: 'Centre' }
  return labels[id] ?? id
}
</script>
