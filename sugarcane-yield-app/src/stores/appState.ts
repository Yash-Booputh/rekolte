import { ref } from 'vue'

/** Bumped whenever the active model changes. Watchers on other pages use this to refresh. */
export const modelActivatedAt = ref(0)
