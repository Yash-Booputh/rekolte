<template>
  <!-- Explicit pixel height so Leaflet has a real container to measure -->
  <div ref="mapEl" style="width:100%; height:100%; min-height:400px; border-radius:0.75rem; z-index:0;"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import L from 'leaflet'
import type { Region } from '@/data/mockData'

// Fix Leaflet's broken default marker icon paths in Vite
import markerIcon2x   from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon     from 'leaflet/dist/images/marker-icon.png'
import markerShadow   from 'leaflet/dist/images/marker-shadow.png'
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({ iconUrl: markerIcon, iconRetinaUrl: markerIcon2x, shadowUrl: markerShadow })

// ── Mauritius bounding box ───────────────────────────────────
const MRU_BOUNDS = L.latLngBounds(
  L.latLng(-20.53, 57.27),   // SW corner
  L.latLng(-19.96, 57.80),   // NE corner
)

const TILES = {
  heatmap:   { url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',  attr: '© OpenStreetMap © CARTO' },
  satellite: { url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr: '© Esri' },
}

interface RegionValue { region: Region; tch: number }

const props = defineProps<{
  regionValues: RegionValue[]
  selectedRegion?: Region | null
  mode?: 'heatmap' | 'satellite'
}>()

const emit = defineEmits<{ regionClick: [region: Region] }>()

const mapEl = ref<HTMLElement | null>(null)
let map: L.Map | null = null
let geojsonLayer: L.GeoJSON | null = null
let tileLayer: L.TileLayer | null = null

// ── Colour helpers ───────────────────────────────────────────
function tchColor(tch: number) {
  if (tch >= 80) return '#2d5016'
  if (tch >= 70) return '#4a8524'
  if (tch >= 60) return '#C8891A'
  return '#dc2626'
}
function tchOpacity(tch: number) {
  if (tch >= 80) return 0.75
  if (tch >= 70) return 0.62
  if (tch >= 60) return 0.55
  return 0.50
}

function styleFeature(feature: any): L.PathOptions {
  const id  = feature.properties.region as Region
  const val = props.regionValues.find(r => r.region === id)
  const tch = val?.tch ?? 60
  return {
    fillColor:   tchColor(tch),
    fillOpacity: tchOpacity(tch),
    color:       props.selectedRegion === id ? '#C8891A' : '#ffffff',
    weight:      props.selectedRegion === id ? 3 : 1.5,
    opacity: 1,
  }
}

function onEachFeature(feature: any, layer: L.Layer) {
  const id    = feature.properties.region as Region
  const label = feature.properties.label as string
  const val   = props.regionValues.find(r => r.region === id)
  const tch   = val?.tch ?? '—'

  ;(layer as L.Path).bindTooltip(
    `<strong style="color:#2d5016">${label} Region</strong><br/>TCH: <b>${tch}</b>`,
    { sticky: true, className: 'rekolte-tooltip', direction: 'top' }
  )

  layer.on({
    mouseover(e) {
      const l = e.target as L.Path
      l.setStyle({ weight: 3, fillOpacity: Math.min(tchOpacity(val?.tch ?? 60) + 0.15, 0.95) })
      l.bringToFront()
    },
    mouseout(e) { geojsonLayer?.resetStyle(e.target) },
    click()     { emit('regionClick', id) },
  })
}

// ── Map init ─────────────────────────────────────────────────
async function loadMap() {
  if (!mapEl.value) return

  // Wait for the DOM to have real dimensions
  await nextTick()

  map = L.map(mapEl.value, {
    center: MRU_BOUNDS.getCenter(),
    zoom: 10,
    minZoom: 9,           // prevent zooming out past island
    maxZoom: 14,
    maxBounds: MRU_BOUNDS,
    maxBoundsViscosity: 1.0,  // hard lock — can't pan outside
    zoomControl: false,
    attributionControl: true,
  })

  const tile = TILES[props.mode ?? 'heatmap']
  tileLayer = L.tileLayer(tile.url, {
    attribution: tile.attr,
    maxZoom: 14,
  }).addTo(map)

  L.control.zoom({ position: 'bottomright' }).addTo(map)

  // Load GeoJSON
  const res  = await fetch('/mauritius_regions.geojson')
  const data = await res.json()

  geojsonLayer = L.geoJSON(data, {
    style: styleFeature,
    onEachFeature,
  }).addTo(map)

  // Fit tightly to island and lock
  map.fitBounds(MRU_BOUNDS, { padding: [10, 10], animate: false })

  // Leaflet needs this if the container was hidden or had no size at init time
  map.invalidateSize()
}

function refreshStyles() {
  geojsonLayer?.setStyle(styleFeature)
}

function swapTile() {
  if (!map || !tileLayer) return
  map.removeLayer(tileLayer)
  const tile = TILES[props.mode ?? 'heatmap']
  tileLayer = L.tileLayer(tile.url, { attribution: tile.attr, maxZoom: 14 }).addTo(map)
  geojsonLayer?.bringToFront()
}

onMounted(loadMap)
onUnmounted(() => { map?.remove(); map = null })
watch(() => props.regionValues, refreshStyles, { deep: true })
watch(() => props.selectedRegion, refreshStyles)
watch(() => props.mode, swapTile)
</script>

<style>
.rekolte-tooltip {
  background: white !important;
  border: 1px solid #e0e4dd !important;
  border-radius: 8px !important;
  padding: 8px 12px !important;
  box-shadow: 0 4px 12px rgba(45, 80, 22, 0.18) !important;
  font-family: 'Work Sans', sans-serif !important;
  font-size: 12px;
  color: #1e293b;
}
/* Hide the tooltip arrow */
.rekolte-tooltip::before { display: none !important; }
.leaflet-tooltip-top::before { display: none !important; }

/* Ensure tiles sit below our overlaid legend */
.leaflet-pane { z-index: 1 !important; }
.leaflet-top, .leaflet-bottom { z-index: 2 !important; }
</style>
