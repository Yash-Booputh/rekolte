<template>
  <div class="min-h-screen bg-parchment flex items-center justify-center px-4">
    <div class="w-full max-w-md">
      <!-- Logo card -->
      <div class="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
        <!-- Header band -->
        <div class="bg-primary px-8 py-10 text-center">
          <div class="inline-flex items-center justify-center bg-accent/20 rounded-2xl p-4 mb-4">
            <span class="material-symbols-outlined text-white text-4xl">agriculture</span>
          </div>
          <h1 class="text-3xl font-black text-white uppercase tracking-tight">Rékolte</h1>
          <p class="text-white/70 mt-1 text-sm font-medium">Sugarcane Yield Prediction System</p>
          <p class="text-white/50 mt-1 text-xs">Mauritius · Middlesex University</p>
        </div>

        <!-- Sign-in section -->
        <div class="px-8 py-10 flex flex-col items-center gap-6">
          <div class="text-center">
            <h2 class="text-lg font-bold text-slate-800">Welcome back</h2>
            <p class="text-slate-500 text-sm mt-1">Sign in to access yield predictions and regional data</p>
          </div>

          <div v-if="error" class="w-full bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
            {{ error }}
          </div>

          <!-- Google Sign-In button -->
          <div id="google-signin-btn" class="w-full flex justify-center"></div>

          <div v-if="loading" class="flex items-center gap-2 text-slate-500 text-sm">
            <svg class="animate-spin h-4 w-4 text-primary" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            Signing in...
          </div>

          <p class="text-xs text-slate-400 text-center">
            Access is restricted to authorised agricultural personnel.<br/>
            Contact your administrator if you need access.
          </p>
        </div>
      </div>

      <p class="text-center text-xs text-slate-400 mt-6">
        © 2025 Rékolte · CST3990 Final Year Project · Middlesex University Mauritius
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authGoogle } from '@/services/api'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { login, isLoggedIn } = useAuth()
const loading = ref(false)
const error = ref('')

onMounted(() => {
  if (isLoggedIn.value) {
    router.replace('/dashboard')
    return
  }

  // Load Google Identity Services script
  const script = document.createElement('script')
  script.src = 'https://accounts.google.com/gsi/client'
  script.async = true
  script.defer = true
  script.onload = initGoogle
  document.head.appendChild(script)
})

function initGoogle() {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
  if (!clientId || !(window as any).google) return

  ;(window as any).google.accounts.id.initialize({
    client_id: clientId,
    callback: handleCredential,
  })

  ;(window as any).google.accounts.id.renderButton(
    document.getElementById('google-signin-btn'),
    {
      theme: 'outline',
      size: 'large',
      width: 320,
      text: 'signin_with',
      shape: 'rectangular',
    }
  )
}

async function handleCredential(response: { credential: string }) {
  loading.value = true
  error.value = ''
  try {
    const result = await authGoogle(response.credential)
    login(result.token, result.user)
    router.replace('/dashboard')
  } catch (e: any) {
    error.value = e.message || 'Sign-in failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>
