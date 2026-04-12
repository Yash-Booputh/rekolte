<template>
  <nav class="md:hidden fixed bottom-0 inset-x-0 z-50 bg-primary border-t border-white/10 flex items-stretch" style="padding-bottom: env(safe-area-inset-bottom)">
    <router-link
      v-for="tab in tabs" :key="tab.to" :to="tab.to"
      class="flex-1 flex flex-col items-center justify-center py-2 gap-0.5 text-white/60 transition-colors"
      active-class="!text-accent"
    >
      <span class="material-symbols-outlined text-xl">{{ tab.icon }}</span>
      <span class="text-[10px] font-bold">{{ tab.label }}</span>
    </router-link>
  </nav>
</template>

<script setup lang="ts">
const tabs = [
  { to: '/dashboard', icon: 'map',           label: 'Dashboard' },
  { to: '/regions',   icon: 'analytics',     label: 'Regions'   },
  { to: '/history',   icon: 'table_chart',   label: 'History'   },
  { to: '/compare',   icon: 'compare_arrows',label: 'Compare'   },
]
</script>
