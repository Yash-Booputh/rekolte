<template>
  <footer class="bg-primary text-white/75 shrink-0">
    <div class="px-6 py-4 grid grid-cols-1 md:grid-cols-3 gap-4 items-start text-[11px]">

      <!-- Left: Branding -->
      <div class="flex flex-col gap-0.5">
        <router-link to="/dashboard" class="flex items-center gap-1.5 mb-1 hover:opacity-90 transition-opacity">
          <img src="/logo.png" alt="Rékolte" class="h-10 w-10 rounded-lg object-cover" />
          <span class="text-white font-black text-sm tracking-tight">Rékolte</span>
        </router-link>
        <span>Student ID: M01006629</span>
        <span>BSc Computer Science</span>
        <span class="mt-0.5">© {{ year }} Middlesex University Mauritius</span>
        <span>Costal Road, Flic en Flac</span>
      </div>

      <!-- Centre: Contact -->
      <div class="flex flex-col gap-1">
        <span class="text-white font-bold uppercase tracking-widest text-[9px] mb-0.5">Contact</span>
        <a href="tel:+23059082464" class="flex items-center gap-1.5 hover:text-white transition-colors">
          <span class="material-symbols-outlined text-accent" style="font-size:14px">call</span>
          (+230) 590 82464
        </a>
        <a href="mailto:yashvinbooputh2@gmail.com" class="flex items-start gap-1.5 hover:text-white transition-colors break-all">
          <span class="material-symbols-outlined text-accent shrink-0" style="font-size:14px">mail</span>
          yashvinbooputh2@gmail.com
        </a>
      </div>

      <!-- Right: Industry links -->
      <div class="flex flex-col gap-1">
        <span class="text-white font-bold uppercase tracking-widest text-[9px] mb-0.5">Industry Resources</span>
        <a
          v-for="link in links" :key="link.name"
          :href="link.url" target="_blank" rel="noopener noreferrer"
          class="flex items-center gap-1.5 hover:text-white transition-colors"
        >
          <span class="material-symbols-outlined text-accent" style="font-size:14px">open_in_new</span>
          {{ link.name }}
        </a>
      </div>

    </div>

    <div class="border-t border-white/10 py-1.5 text-center text-white/35 text-[9px]">
      Predicting Sugarcane Yield in Mauritius Using Satellite Imagery and Open-Source ML · CST3990
    </div>
  </footer>
</template>

<script setup lang="ts">
const year = new Date().getFullYear()

const links = [
  { name: 'MSIRI', url: 'https://www.msiri.mu' },
  { name: 'Mauritius Chamber of Agriculture', url: 'https://www.mauritiuschamberofagriculture.com' },
  { name: 'Medine Sugarcane', url: 'https://www.medine.com' },
  { name: 'Omnicane', url: 'https://www.omnicane.com' },
]
</script>
