<template>
  <header class="flex items-center justify-between bg-primary text-white px-8 py-4 shadow-lg sticky top-0 z-50">
    <!-- Logo -->
    <router-link to="/dashboard" class="flex items-center gap-3 hover:opacity-90 transition-opacity">
      <img src="/logo.png" alt="Rékolte" class="h-14 w-14 rounded-xl object-cover" />
      <h1 class="text-2xl font-black tracking-tight uppercase">Rékolte</h1>
    </router-link>

    <!-- Nav links -->
    <nav class="hidden md:flex items-center gap-10">
      <router-link
        v-for="link in links" :key="link.to" :to="link.to"
        class="text-sm font-medium text-white/80 hover:text-white transition-colors"
        active-class="!font-bold border-b-2 border-accent pb-1 !text-white"
      >{{ link.label }}</router-link>
    </nav>

    <!-- Right side -->
    <div class="flex items-center gap-4">
      <!-- Notification bell -->
      <div class="relative" v-click-outside="() => notifOpen = false">
        <button
          class="p-2 hover:bg-white/10 rounded-full transition-colors relative"
          @click="notifOpen = !notifOpen"
        >
          <span class="material-symbols-outlined">notifications</span>
          <span
            v-if="unreadCount > 0"
            class="absolute top-1 right-1 size-2 bg-accent rounded-full border-2 border-primary"
          ></span>
        </button>

        <!-- Notification dropdown -->
        <div
          v-if="notifOpen"
          class="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden z-[9999]"
        >
          <div class="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <h4 class="text-sm font-bold text-slate-800">Notifications</h4>
            <button
              v-if="unreadCount > 0"
              class="text-xs text-accent font-semibold hover:underline"
              @click="markAllRead"
            >Mark all read</button>
          </div>
          <div class="max-h-72 overflow-y-auto">
            <div v-if="notifications.length === 0" class="px-4 py-6 text-center text-slate-400 text-sm">
              No notifications yet
            </div>
            <div
              v-for="n in notifications" :key="n.id"
              class="flex gap-3 px-4 py-3 border-b border-slate-50 hover:bg-slate-50 cursor-pointer"
              :class="!n.read ? 'bg-primary/5' : ''"
              @click="markRead(n.id)"
            >
              <span class="material-symbols-outlined text-primary mt-0.5 shrink-0 text-base">
                {{ notifIcon(n.type) }}
              </span>
              <div class="min-w-0">
                <p class="text-xs text-slate-700 font-medium leading-snug">{{ n.message }}</p>
                <p class="text-[10px] text-slate-400 mt-0.5">{{ timeAgo(n.created_at) }}</p>
              </div>
              <span v-if="!n.read" class="size-2 bg-accent rounded-full mt-1.5 shrink-0"></span>
            </div>
          </div>
        </div>
      </div>

      <div class="h-8 w-px bg-white/20 mx-1"></div>

      <!-- User avatar + dropdown -->
      <div class="relative" v-click-outside="() => userOpen = false">
        <button
          class="flex items-center gap-3 cursor-pointer hover:bg-white/10 rounded-lg px-2 py-1 transition-colors"
          @click="userOpen = !userOpen"
        >
          <div class="text-right hidden sm:block">
            <p class="text-xs font-bold">{{ user?.name ?? 'User' }}</p>
            <p class="text-[10px] text-white/60 capitalize">{{ user?.role ?? 'agronomist' }}</p>
          </div>
          <div class="size-9 rounded-full border-2 border-accent overflow-hidden bg-white/20 flex items-center justify-center">
            <img v-if="user?.picture" :src="user.picture" class="size-full object-cover" referrerpolicy="no-referrer" />
            <span v-else class="material-symbols-outlined text-sm">person</span>
          </div>
          <span class="material-symbols-outlined text-xs text-white/60">expand_more</span>
        </button>

        <!-- User dropdown -->
        <div
          v-if="userOpen"
          class="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden z-[9999]"
        >
          <div class="px-4 py-3 border-b border-slate-100">
            <p class="text-sm font-bold text-slate-800 truncate">{{ user?.name }}</p>
            <p class="text-xs text-slate-400 truncate">{{ user?.email }}</p>
          </div>
          <div class="py-1">
            <button
              class="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
              @click="openUploadModel"
            >
              <span class="material-symbols-outlined text-base text-slate-400">upload</span>
              Upload New Model
            </button>
            <button
              class="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
              @click="openSettings"
            >
              <span class="material-symbols-outlined text-base text-slate-400">settings</span>
              Settings
            </button>
            <button
              class="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors"
              @click="handleLogout"
            >
              <span class="material-symbols-outlined text-base">logout</span>
              Sign out
            </button>
          </div>
        </div>
      </div>
    </div>
  </header>

  <!-- Upload New Model modal -->
  <div v-if="uploadModelOpen" class="fixed inset-0 bg-black/40 z-[10000] flex items-center justify-center px-4">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
      <div class="bg-primary px-6 py-4 flex items-center justify-between">
        <h3 class="text-white font-bold">Upload New Model</h3>
        <button @click="uploadModelOpen = false" class="text-white/70 hover:text-white">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <div class="p-6 space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-xs font-bold text-slate-500 uppercase mb-1 block">Model Type</label>
            <select v-model="uploadType" class="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-primary bg-white outline-none focus:ring-2 focus:ring-primary/20">
              <option value="RandomForest">Random Forest</option>
              <option value="XGBoost">XGBoost</option>
            </select>
          </div>
          <div>
            <label class="text-xs font-bold text-slate-500 uppercase mb-1 block">LOSO R²</label>
            <input v-model="uploadMetrics.loso_r2" type="number" step="0.0001" placeholder="e.g. 0.5484" class="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20" />
          </div>
          <div>
            <label class="text-xs font-bold text-slate-500 uppercase mb-1 block">LOSO RMSE</label>
            <input v-model="uploadMetrics.loso_rmse" type="number" step="0.0001" placeholder="e.g. 7.2863" class="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20" />
          </div>
          <div>
            <label class="text-xs font-bold text-slate-500 uppercase mb-1 block">LOSO MAE</label>
            <input v-model="uploadMetrics.loso_mae" type="number" step="0.0001" placeholder="e.g. 5.9433" class="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20" />
          </div>
        </div>
        <div>
          <label class="text-xs font-bold text-slate-500 uppercase mb-1 block">Model File (.joblib or .ubj)</label>
          <input type="file" accept=".joblib,.ubj" @change="onFileSelect" class="w-full text-sm text-slate-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-primary file:text-white cursor-pointer" />
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button @click="uploadModelOpen = false" class="px-5 py-2 rounded-lg text-sm font-bold text-slate-600 hover:bg-slate-100 transition-colors">Cancel</button>
          <button
            class="flex items-center gap-2 px-6 py-2 bg-primary text-white rounded-lg font-bold text-sm hover:bg-primary/90 disabled:opacity-50 transition-colors"
            :disabled="uploading || !selectedFile"
            @click="submitUpload"
          >
            <svg v-if="uploading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            <span class="material-symbols-outlined text-sm" v-else>upload</span>
            {{ uploading ? 'Uploading…' : 'Upload Model' }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Settings modal -->
  <div v-if="settingsOpen" class="fixed inset-0 bg-black/40 z-[10000] flex items-center justify-center px-4">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden">
      <div class="bg-primary px-6 py-4 flex items-center justify-between">
        <h3 class="text-white font-bold">Account Settings</h3>
        <button @click="settingsOpen = false" class="text-white/70 hover:text-white">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <div class="p-6 flex flex-col items-center gap-4">
        <div class="size-20 rounded-full border-4 border-primary overflow-hidden">
          <img v-if="user?.picture" :src="user.picture" class="size-full object-cover" referrerpolicy="no-referrer" />
          <span v-else class="material-symbols-outlined text-4xl text-primary">person</span>
        </div>
        <div class="text-center">
          <p class="font-bold text-slate-800 text-lg">{{ user?.name }}</p>
          <p class="text-slate-500 text-sm">{{ user?.email }}</p>
          <span class="inline-block mt-2 px-3 py-1 bg-primary/10 text-primary text-xs font-bold rounded-full capitalize">
            {{ user?.role }}
          </span>
        </div>
        <p class="text-xs text-slate-400 text-center">
          Profile information is managed through your Google account.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { getNotifications, markNotificationRead, markAllNotificationsRead, uploadModel } from '@/services/api'
import type { Notification } from '@/services/api'

const router = useRouter()
const { user, logout } = useAuth()

const notifOpen = ref(false)
const userOpen = ref(false)
const settingsOpen = ref(false)
const uploadModelOpen = ref(false)
const uploading = ref(false)
const selectedFile = ref<File | null>(null)
const uploadType = ref('XGBoost')
const uploadMetrics = ref({ loso_r2: '', loso_rmse: '', loso_mae: '' })
const notifications = ref<Notification[]>([])

const links = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/regions',   label: 'Regions' },
  { to: '/history',   label: 'History' },
  { to: '/compare',   label: 'Compare' },
]

const unreadCount = computed(() => notifications.value.filter(n => !n.read).length)

onMounted(fetchNotifications)

async function fetchNotifications() {
  try {
    notifications.value = await getNotifications()
  } catch { /* silently fail */ }
}

async function markRead(id: string) {
  await markNotificationRead(id)
  const n = notifications.value.find(n => n.id === id)
  if (n) n.read = true
}

async function markAllRead() {
  await markAllNotificationsRead()
  notifications.value.forEach(n => n.read = true)
}

function openSettings() {
  userOpen.value = false
  settingsOpen.value = true
}

function openUploadModel() {
  userOpen.value = false
  uploadModelOpen.value = true
}

function onFileSelect(e: Event) {
  selectedFile.value = (e.target as HTMLInputElement).files?.[0] ?? null
}

async function submitUpload() {
  if (!selectedFile.value) return
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', selectedFile.value)
    fd.append('type', uploadType.value)
    fd.append('loso_r2', String(uploadMetrics.value.loso_r2))
    fd.append('loso_rmse', String(uploadMetrics.value.loso_rmse))
    fd.append('loso_mae', String(uploadMetrics.value.loso_mae))
    await uploadModel(fd)
    uploadModelOpen.value = false
    selectedFile.value = null
    uploadMetrics.value = { loso_r2: '', loso_rmse: '', loso_mae: '' }
  } catch (e: any) {
    alert('Upload failed: ' + e.message)
  } finally {
    uploading.value = false
  }
}

function handleLogout() {
  logout()
  router.replace('/login')
}

function notifIcon(type: string) {
  const icons: Record<string, string> = {
    prediction: 'analytics',
    model_uploaded: 'upload',
    model_activated: 'verified',
    bulletin_uploaded: 'description',
  }
  return icons[type] ?? 'notifications'
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

// v-click-outside directive
const vClickOutside = {
  mounted(el: HTMLElement, binding: any) {
    ;(el as any)._clickOutside = (e: Event) => {
      if (!el.contains(e.target as Node)) binding.value(e)
    }
    document.addEventListener('mousedown', (el as any)._clickOutside)
  },
  unmounted(el: HTMLElement) {
    document.removeEventListener('mousedown', (el as any)._clickOutside)
  },
}
</script>
