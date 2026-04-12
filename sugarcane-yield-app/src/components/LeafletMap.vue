<template>
  <!-- Explicit pixel height so Leaflet has a real container to measure -->
  <div ref="mapEl" style="width:100%; height:100%; min-height:400px; border-radius:0.75rem; z-index:0;"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import L from 'leaflet'
import type { Region } from '@/data/mockData'
import { REGION_COLORS } from '@/utils/regionColors'

// Fix Leaflet's broken default marker icon paths in Vite
import markerIcon2x   from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon     from 'leaflet/dist/images/marker-icon.png'
import markerShadow   from 'leaflet/dist/images/marker-shadow.png'
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({ iconUrl: markerIcon, iconRetinaUrl: markerIcon2x, shadowUrl: markerShadow })

// ── Mauritius bounding box ───────────────────────────────────
const MRU_BOUNDS = L.latLngBounds(
  L.latLng(-21.20, 56.50),   // SW — generous ocean buffer
  L.latLng(-19.30, 58.60),   // NE — generous ocean buffer
)

const TILES = {
  heatmap:   { url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', attr: '© OpenStreetMap contributors', subdomains: 'abc' },
  satellite: { url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr: '© Esri', subdomains: '' },
}

interface RegionValue { region: Region; tch: number; model?: string }

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
let hoveredLayer: L.Path | null = null
let estateMarkerLayers: L.Marker[] = []


function styleFeature(feature: any): L.PathOptions {
  const id         = feature.properties.region as Region
  const selected   = props.selectedRegion === id
  const isSatellite = (props.mode ?? 'satellite') === 'satellite'
  return {
    fillColor:   REGION_COLORS[id] ?? '#888888',
    fillOpacity: selected ? 0.75 : 0.50,
    color:       selected
      ? (isSatellite ? 'rgba(255,255,255,0.9)' : 'rgba(15,23,42,0.85)')
      : (isSatellite ? 'rgba(15,23,42,0.35)'   : 'rgba(15,23,42,0.55)'),
    weight:      selected ? 2.5 : 1.2,
    opacity:     1,
  }
}

function onEachFeature(feature: any, layer: L.Layer) {
  const id    = feature.properties.region as Region
  const label = feature.properties.label as string

  ;(layer as L.Path).bindTooltip('', { sticky: true, className: 'rekolte-tooltip', direction: 'top' })

  layer.on({
    mouseover(e) {
      const l = e.target as L.Path
      // Reset any previously stuck hover
      if (hoveredLayer && hoveredLayer !== l) geojsonLayer?.resetStyle(hoveredLayer)
      hoveredLayer = l
      const hoverColor = (props.mode ?? 'satellite') === 'satellite'
        ? 'rgba(255,255,255,0.8)'
        : 'rgba(15,23,42,0.8)'
      l.setStyle({ weight: 2, fillOpacity: 0.72, color: hoverColor })
      l.bringToFront()
      const rv = props.regionValues.find(r => r.region === id)
      const tch = rv?.tch ?? '—'
      const model = rv?.model ?? ''
      ;(l as any).getTooltip()?.setContent(
        `<strong style="color:#2d5016">${label} Region</strong><br/>TCH: <b>${tch}</b>${model ? `<br/><span style="color:#888;font-size:11px">${model}</span>` : ''}`
      )
    },
    mouseout(e) { geojsonLayer?.resetStyle(e.target); hoveredLayer = null },
    click(e)    {
      L.DomEvent.stopPropagation(e)
      emit('regionClick', id)
      map?.fitBounds((e.target as L.Polygon).getBounds(), { padding: [10, 10], maxZoom: 14 })
    },
  })
}

// ── Estate / mill marker data ────────────────────────────────
const ESTATE_MARKERS = [
  { name: 'Terragen',                        region: 'NORD'  as Region, lat: -20.0676,           lng: 57.5991,           type: 'mill' as const, image: '/terra.png'    },
  { name: 'Alteo (FUEL)',                    region: 'EST'   as Region, lat: -20.2199,           lng: 57.6917,           type: 'mill' as const, image: '/alteo.png'    },
  { name: 'Médine Group',                    region: 'OUEST' as Region, lat: -20.2612,           lng: 57.3941,           type: 'farm' as const, image: '/medine.png'   },
  { name: 'Omnicane',                        region: 'SUD'   as Region, lat: -20.4290,           lng: 57.6502,           type: 'mill' as const, image: '/omnicane.png' },
  { name: 'MCIA',                            region: 'OUEST' as Region, lat: -20.238351468846233, lng: 57.496755557864894, type: 'govt' as const, image: '/mcia.png'    },
  { name: 'Mauritius Chamber of Agriculture',region: 'OUEST' as Region, lat: -20.225417541038812, lng: 57.53335132363508,  type: 'govt' as const, image: '/chamber.png' },
]

function millIconSize(zoom: number): number {
  // Snap to 4 discrete sizes to maximise cache hits
  const raw = Math.round(42 - (zoom - 9) * 4.8)
  return Math.round(raw / 6) * 6   // rounds to nearest 6px: 18 / 24 / 30 / 36 / 42
}

const _iconCache = new Map<string, L.DivIcon>()

function makeMillIcon(region: Region, size: number, type: 'mill' | 'farm' | 'govt' = 'mill'): L.DivIcon {
  const cacheKey = `${region}-${size}-${type}`
  if (_iconCache.has(cacheKey)) return _iconCache.get(cacheKey)!

  // Government bodies use a fixed navy color regardless of region
  const color = type === 'govt' ? '#1e3a8a' : (REGION_COLORS[region] ?? '#555')
  const svgSize = Math.round(size * 0.58)

  // Mill icon: two smokestacks + building body + windows + door
  const millSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${svgSize}" height="${svgSize}" fill="white">
    <rect x="3"  y="5"  width="3" height="9" rx="0.8"/>
    <rect x="8"  y="7"  width="3" height="7" rx="0.8"/>
    <rect x="2"  y="14" width="20" height="8" rx="1"/>
    <rect x="4"  y="16" width="2.5" height="2.5" rx="0.4" fill="rgba(0,0,0,0.28)"/>
    <rect x="8"  y="16" width="2.5" height="2.5" rx="0.4" fill="rgba(0,0,0,0.28)"/>
    <rect x="15" y="16" width="3"   height="6"   rx="0.4" fill="rgba(0,0,0,0.28)"/>
  </svg>`

  // Farm/crop icon: sugarcane stalk
  const farmSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${svgSize}" height="${svgSize}" fill="none" stroke="white" stroke-linecap="round">
    <line x1="12" y1="22" x2="12" y2="2" stroke-width="2"/>
    <circle cx="12" cy="7"  r="1.1" fill="white" stroke="none"/>
    <circle cx="12" cy="13" r="1.1" fill="white" stroke="none"/>
    <circle cx="12" cy="19" r="1.1" fill="white" stroke="none"/>
    <path d="M12 7  Q7  5  5  2"  stroke-width="1.6"/>
    <path d="M12 7  Q17 5  19 2"  stroke-width="1.6"/>
    <path d="M12 13 Q6  11 4  8"  stroke-width="1.6"/>
    <path d="M12 13 Q18 11 20 8"  stroke-width="1.6"/>
    <path d="M12 19 Q7  17 5  14" stroke-width="1.6"/>
    <path d="M12 19 Q17 17 19 14" stroke-width="1.6"/>
  </svg>`

  // Government building icon: classical pediment + columns + base
  const govtSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${svgSize}" height="${svgSize}" fill="white">
    <polygon points="12,2 2,8 22,8"/>
    <rect x="3"  y="8"  width="2" height="10"/>
    <rect x="7"  y="8"  width="2" height="10"/>
    <rect x="11" y="8"  width="2" height="10"/>
    <rect x="15" y="8"  width="2" height="10"/>
    <rect x="19" y="8"  width="2" height="10"/>
    <rect x="8"  y="14" width="8"  height="4" fill="rgba(0,0,0,0.25)"/>
    <rect x="1"  y="18" width="22" height="2.5" rx="0.5"/>
  </svg>`

  const svg = type === 'farm' ? farmSvg : type === 'govt' ? govtSvg : millSvg

  // Government markers use a rounded-square shape to distinguish from industry circles
  const borderRadius = type === 'govt' ? '28%' : '50%'
  const half = size / 2
  const icon = L.divIcon({
    html: `<div style="
      background:${color};
      width:${size}px;height:${size}px;
      border-radius:${borderRadius};
      border:2px solid white;
      box-shadow:0 2px 8px rgba(0,0,0,0.45);
      display:flex;align-items:center;justify-content:center;
    ">${svg}</div>`,
    className: '',
    iconSize:   [size, size],
    iconAnchor: [half, half],
  })
  _iconCache.set(cacheKey, icon)
  return icon
}

function updateEstateIconSizes() {
  if (!map) return
  const zoom = map.getZoom()
  const size = millIconSize(zoom)
  estateMarkerLayers.forEach((marker, i) => {
    marker.setIcon(makeMillIcon(ESTATE_MARKERS[i].region, size, ESTATE_MARKERS[i].type))
  })
}

// ── Region metadata ──────────────────────────────────────────
const REGION_META: Record<string, { label: string }> = {
  NORD:   { label: 'Nord' },
  SUD:    { label: 'Sud' },
  EST:    { label: 'Est' },
  OUEST:  { label: 'Ouest' },
  CENTRE: { label: 'Centre' },
}

// ── Load real GEE boundary files and merge into FeatureCollection ──
async function loadBoundaries() {
  const regions = ['NORD', 'SUD', 'EST', 'OUEST', 'CENTRE'] as const
  const results = await Promise.all(
    regions.map(r => fetch(`${import.meta.env.PROD ? '/rekolte/' : '/'}mapping_boundaries/${r}_boundary.geojson`).then(res => res.json()))
  )
  const features = results.map((fc, i) => {
    const region = regions[i]
    const feature = fc.features[0]
    feature.properties = { region, label: REGION_META[region].label }
    return feature
  })
  return { type: 'FeatureCollection', features }
}

// ── Map init ─────────────────────────────────────────────────
async function loadMap() {
  if (!mapEl.value) return

  // Wait for the DOM to have real dimensions
  await nextTick()

  map = L.map(mapEl.value, {
    center: MRU_BOUNDS.getCenter(),
    zoom: 10.59,
    zoomSnap: 0.25,
    zoomDelta: 0.5,
    minZoom: 9,
    maxZoom: 14,
    maxBounds: MRU_BOUNDS,
    maxBoundsViscosity: 0.7,
    zoomControl: false,
    attributionControl: true,
    preferCanvas: true,
  })

  const tile = TILES[props.mode ?? 'satellite']
  tileLayer = L.tileLayer(tile.url, {
    attribution: tile.attr,
    subdomains: tile.subdomains || 'abc',
    maxZoom: 14,
    updateWhenZooming: false,
    keepBuffer: 4,
  }).addTo(map)

  L.control.zoom({ position: 'bottomright' }).addTo(map)

  map.on('click', () => {
    if (hoveredLayer) { geojsonLayer?.resetStyle(hoveredLayer); hoveredLayer = null }
    emit('regionClick', null as any)
  })

  // Load real GEE-exported region boundaries
  const data = await loadBoundaries()

  geojsonLayer = L.geoJSON(data as any, {
    style: styleFeature,
    onEachFeature,
    smoothFactor: 1.5,
  } as any).addTo(map)

  // ── Estate / mill markers ──────────────────────────────────
  const initSize = millIconSize(map.getZoom())
  estateMarkerLayers = []
  for (const estate of ESTATE_MARKERS) {
    const typeLabel = estate.type === 'farm' ? 'Sugarcane Farm' : estate.type === 'govt' ? 'Government Body' : 'Sugar Mill'
    const marker = L.marker([estate.lat, estate.lng], { icon: makeMillIcon(estate.region, initSize, estate.type) })
      .bindTooltip(
        `<div class="rekolte-estate-card">
          <img src="${estate.image}" alt="${estate.name}" />
          <div class="rekolte-estate-body">
            <strong>${estate.name}</strong>
            <span>${typeLabel} &middot; ${estate.region} Region</span>
          </div>
        </div>`,
        { className: 'rekolte-tooltip rekolte-estate-tooltip', direction: 'top', offset: [0, -14], sticky: false }
      )
      .addTo(map!)
    estateMarkerLayers.push(marker)
  }
  map.on('zoomend', updateEstateIconSizes)

  // Leaflet needs this if the container was hidden or had no size at init time
  map.invalidateSize()
}

function refreshStyles() {
  geojsonLayer?.setStyle(styleFeature)
}

function swapTile() {
  if (!map || !tileLayer) return
  map.removeLayer(tileLayer)
  const tile = TILES[props.mode ?? 'satellite']
  tileLayer = L.tileLayer(tile.url, { attribution: tile.attr, subdomains: tile.subdomains || 'abc', maxZoom: 14, updateWhenZooming: false, keepBuffer: 4 }).addTo(map)
  geojsonLayer?.setStyle(styleFeature)
  geojsonLayer?.bringToFront()
}

onMounted(loadMap)
onUnmounted(() => { map?.remove(); map = null; _iconCache.clear() })
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

/* Rich estate card tooltip */
.rekolte-estate-tooltip {
  padding: 0 !important;
  overflow: hidden !important;
  width: 200px !important;
}
.rekolte-estate-card img {
  width: 200px;
  height: 120px;
  object-fit: cover;
  display: block;
}
.rekolte-estate-body {
  padding: 8px 10px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.rekolte-estate-body strong {
  color: #2d5016;
  font-size: 13px;
}
.rekolte-estate-body span {
  color: #64748b;
  font-size: 11px;
}

/* Hide the tooltip arrow */
.rekolte-tooltip::before { display: none !important; }
.leaflet-tooltip-top::before { display: none !important; }

/* Ensure tiles sit below our overlaid legend */
.leaflet-pane { z-index: 1 !important; }
.leaflet-top, .leaflet-bottom { z-index: 2 !important; }

/* Remove Leaflet's default focus rectangle on clicked regions */
.leaflet-interactive:focus { outline: none !important; }
</style>
