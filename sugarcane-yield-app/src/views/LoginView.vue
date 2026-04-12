<template>
  <ion-page>
  <div class="min-h-screen relative overflow-hidden flex items-center justify-center px-4">

    <!-- ── Sugarcane field photo background ─────────────────────────────── -->
    <div class="absolute inset-0 bg-cover bg-center bg-no-repeat" :style="`background-image: url('${baseUrl}login.jpg')`"></div>
    <!-- Dark overlay for readability -->
    <div class="absolute inset-0 bg-black/55"></div>
    <!-- Subtle green tint to tie into brand -->
    <div class="absolute inset-0 bg-gradient-to-br from-[#0a1f05]/40 via-transparent to-[#0d2a07]/50"></div>
    <!-- Ground fog strip at bottom -->
    <div class="absolute bottom-0 inset-x-0 h-40 bg-gradient-to-t from-black/50 to-transparent pointer-events-none"></div>

    <!-- ── Login card ───────────────────────────────────────────────────── -->
    <div class="relative z-10 w-full max-w-md">
      <div class="bg-white rounded-2xl shadow-2xl border border-white/20 overflow-hidden">

        <!-- Header band -->
        <div class="bg-primary px-8 py-10 text-center relative overflow-hidden">
          <div class="absolute inset-0 opacity-10" style="background-image: repeating-linear-gradient(45deg, transparent, transparent 10px, white 10px, white 11px)"></div>
          <img src="/logo.png" alt="Rékolte" class="h-20 w-20 rounded-2xl object-cover mx-auto mb-4 shadow-lg ring-2 ring-white/20" />
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

          <!-- Google Sign-In button (web) / native button (Android) -->
          <div v-if="!isNative" id="google-signin-btn" class="w-full flex justify-center"></div>
          <button
            v-if="isNative"
            class="w-full flex items-center justify-center gap-3 border border-slate-300 rounded-lg px-6 py-3 text-sm font-semibold text-slate-700 bg-white hover:bg-slate-50 transition-colors shadow-sm"
            :disabled="loading"
            @click="signInNative"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
              <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
              <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
              <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
              <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 6.29C4.672 4.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
            </svg>
            Sign in with Google
          </button>

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

      <p class="text-center text-xs text-white/40 mt-6">
        © 2026 Rékolte · CST3990 Final Year Project · Middlesex University Mauritius
      </p>
    </div>

  </div>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { IonPage } from '@ionic/vue'
import { useRouter } from 'vue-router'
import { Capacitor } from '@capacitor/core'
import { authGoogle } from '@/services/api'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { login, isLoggedIn } = useAuth()
const baseUrl = import.meta.env.BASE_URL
const loading = ref(false)
const error = ref('')
const isNative = Capacitor.isNativePlatform()

onMounted(() => {
  if (isLoggedIn.value) {
    router.replace('/dashboard')
    return
  }

  // Web-only: load GSI button
  if (!isNative) {
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    script.onload = initGoogle
    document.head.appendChild(script)
  }
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

async function signInNative() {
  loading.value = true
  error.value = ''
  try {
    const { GoogleAuth } = await import('@codetrix-studio/capacitor-google-auth')
    await GoogleAuth.initialize({
      clientId: import.meta.env.VITE_GOOGLE_CLIENT_ID,
      scopes: ['profile', 'email'],
      grantOfflineAccess: false,
    })
    const googleUser = await GoogleAuth.signIn()
    // Use the ID token as credential — same flow as web GSI
    const idToken = googleUser.authentication.idToken
    if (!idToken) throw new Error('No ID token returned from Google.')
    const result = await authGoogle(idToken)
    login(result.token, result.user)
    router.replace('/dashboard')
  } catch (e: any) {
    if (e?.message !== 'The user canceled the sign-in flow.') {
      error.value = e.message || 'Sign-in failed. Please try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>
