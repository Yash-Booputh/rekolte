import { ref, computed } from 'vue'
import type { UserInfo } from '@/services/api'

const _user = ref<UserInfo | null>(null)
const _token = ref<string | null>(null)

// Hydrate from localStorage on first import
const storedUser = localStorage.getItem('rekolte_user')
const storedToken = localStorage.getItem('rekolte_token')
if (storedUser && storedToken) {
  try {
    _user.value = JSON.parse(storedUser)
    _token.value = storedToken
  } catch {
    localStorage.removeItem('rekolte_user')
    localStorage.removeItem('rekolte_token')
  }
}

export function useAuth() {
  const user = computed(() => _user.value)
  const token = computed(() => _token.value)
  const isLoggedIn = computed(() => !!_token.value && !!_user.value)

  function login(token: string, user: UserInfo) {
    _token.value = token
    _user.value = user
    localStorage.setItem('rekolte_token', token)
    localStorage.setItem('rekolte_user', JSON.stringify(user))
  }

  function logout() {
    _token.value = null
    _user.value = null
    localStorage.removeItem('rekolte_token')
    localStorage.removeItem('rekolte_user')
  }

  return { user, token, isLoggedIn, login, logout }
}
