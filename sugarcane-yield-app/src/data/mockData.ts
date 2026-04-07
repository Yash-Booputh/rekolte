// ============================================================
// Rékolte – Mock Data (real historical values from bulletins)
// All TCH, surface, cane/sugar production from season_end_data.csv
// Model metrics are placeholders until training is complete
// ============================================================

export type Region = 'NORD' | 'EST' | 'SUD' | 'OUEST' | 'CENTRE'

export interface RegionMeta {
  id: Region
  label: string
  abbr: string
  description: string
  color: string        // Tailwind/hex for map overlay
  estates: string[]
}

export interface HarvestRecord {
  season: number
  region: Region
  tch: number
  surface_harvested: number
  cane_production: number
  sugar_production: number | null
  extraction_rate: number | null
  tsh: number | null
}

export interface WeeklyRecord {
  week: number
  season: number
  region: Region
  surface_harvested: number
  cane_production: number
  sugar_production: number
  extraction_rate: number
  tch: number
  tsh: number
}

export interface ModelMetrics {
  name: 'RandomForest' | 'XGBoost'
  rmse: number
  mae: number
  r2: number
  featureImportance: { feature: string; importance: number }[]
  predictions: { actual: number; predicted: number }[]
}

// ── Region metadata ─────────────────────────────────────────
export const regions: RegionMeta[] = [
  {
    id: 'NORD',
    label: 'Nord',
    abbr: 'NO',
    description: 'Pamplemousses & Rivière du Rempart',
    color: '#2d5016',
    estates: ['Terra', 'Alteo-Mon Loisir', 'Dom. de Labourdonnais Ltée', 'St Antoine'],
  },
  {
    id: 'EST',
    label: 'Est',
    abbr: 'ES',
    description: 'Flacq & Moka',
    color: '#3a6b1d',
    estates: ['Alteo-Beau Champ', 'Constance', 'Alteo-Union Flacq'],
  },
  {
    id: 'SUD',
    label: 'Sud',
    abbr: 'SU',
    description: 'Grand Port & Savanne',
    color: '#4a8524',
    estates: [
      'Bel Air Agricultural', 'Britannia', 'Mon Trésor', 'Beau Vallon',
      'Rose Belle', 'ER Agri-Savannah', 'Union', 'Senneville Agricultural',
      'St Aubin', 'Agria', 'St Félix',
    ],
  },
  {
    id: 'OUEST',
    label: 'Ouest',
    abbr: 'OU',
    description: 'Black River',
    color: '#C8891A',
    estates: ['Médine'],
  },
  {
    id: 'CENTRE',
    label: 'Centre',
    abbr: 'CE',
    description: 'Plaines Wilhems & Moka',
    color: '#8fa876',
    estates: ['ER Agri-Mon Désert Alma / ENL Agri-St Pierre'],
  },
]

// ── Full historical dataset (18 seasons × 5 regions) ────────
export const historicalData: HarvestRecord[] = [
  // 2008
  { season: 2008, region: 'NORD',   tch: 72.4, surface_harvested: 4666,   cane_production: 337585,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2008, region: 'EST',    tch: 77.5, surface_harvested: 9683,   cane_production: 750412,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2008, region: 'SUD',    tch: 83.3, surface_harvested: 12832,  cane_production: 1069487, sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2008, region: 'OUEST',  tch: 91.8, surface_harvested: 3156,   cane_production: 289567,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2008, region: 'CENTRE', tch: 74.5, surface_harvested: 3337,   cane_production: 248492,  sugar_production: null,  extraction_rate: null,  tsh: null },
  // 2009
  { season: 2009, region: 'NORD',   tch: 83.4, surface_harvested: 4753,   cane_production: 396325,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2009, region: 'EST',    tch: 82.9, surface_harvested: 9916,   cane_production: 821811,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2009, region: 'SUD',    tch: 85.1, surface_harvested: 11669,  cane_production: 992770,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2009, region: 'OUEST',  tch: 92.4, surface_harvested: 3271,   cane_production: 302224,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2009, region: 'CENTRE', tch: 71.3, surface_harvested: 3527,   cane_production: 251655,  sugar_production: null,  extraction_rate: null,  tsh: null },
  // 2010
  { season: 2010, region: 'NORD',   tch: 81.2, surface_harvested: 6670,   cane_production: 541929,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2010, region: 'EST',    tch: 78.5, surface_harvested: 10350,  cane_production: 812724,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2010, region: 'SUD',    tch: 82.0, surface_harvested: 11905,  cane_production: 976596,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2010, region: 'OUEST',  tch: 95.5, surface_harvested: 3121,   cane_production: 298194,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2010, region: 'CENTRE', tch: 69.4, surface_harvested: 2595,   cane_production: 180137,  sugar_production: null,  extraction_rate: null,  tsh: null },
  // 2011
  { season: 2011, region: 'NORD',   tch: 80.9, surface_harvested: 7537,   cane_production: 609491,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2011, region: 'EST',    tch: 77.1, surface_harvested: 10390,  cane_production: 801220,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2011, region: 'SUD',    tch: 83.4, surface_harvested: 11354,  cane_production: 946465,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2011, region: 'OUEST',  tch: 88.3, surface_harvested: 3245,   cane_production: 286395,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2011, region: 'CENTRE', tch: 70.1, surface_harvested: 2615,   cane_production: 183287,  sugar_production: null,  extraction_rate: null,  tsh: null },
  // 2012
  { season: 2012, region: 'NORD',   tch: 74.9, surface_harvested: 7236,   cane_production: 541921,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2012, region: 'EST',    tch: 78.8, surface_harvested: 10269,  cane_production: 808954,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2012, region: 'SUD',    tch: 79.4, surface_harvested: 11456,  cane_production: 909957,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2012, region: 'OUEST',  tch: 83.6, surface_harvested: 3317,   cane_production: 277289,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2012, region: 'CENTRE', tch: 78.4, surface_harvested: 2205,   cane_production: 172867,  sugar_production: null,  extraction_rate: null,  tsh: null },
  // 2013
  { season: 2013, region: 'NORD',   tch: 70.6, surface_harvested: 7262,   cane_production: 512642,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2013, region: 'EST',    tch: 75.7, surface_harvested: 10171,  cane_production: 770239,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2013, region: 'SUD',    tch: 81.8, surface_harvested: 11464,  cane_production: 937858,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2013, region: 'OUEST',  tch: 89.7, surface_harvested: 3392,   cane_production: 304130,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2013, region: 'CENTRE', tch: 67.0, surface_harvested: 2256,   cane_production: 151124,  sugar_production: null,  extraction_rate: null,  tsh: null },
  // 2014
  { season: 2014, region: 'NORD',   tch: 77.4, surface_harvested: 7105,   cane_production: 549732,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2014, region: 'EST',    tch: 87.7, surface_harvested: 9178,   cane_production: 804501,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2014, region: 'SUD',    tch: 88.2, surface_harvested: 11109,  cane_production: 979480,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2014, region: 'OUEST',  tch: 91.1, surface_harvested: 3374,   cane_production: 307316,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2014, region: 'CENTRE', tch: 82.1, surface_harvested: 2211,   cane_production: 181626,  sugar_production: null,  extraction_rate: null,  tsh: null },
  // 2015
  { season: 2015, region: 'NORD',   tch: 78.8, surface_harvested: 7273,   cane_production: 573005,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2015, region: 'EST',    tch: 83.6, surface_harvested: 10488,  cane_production: 876827,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2015, region: 'SUD',    tch: 81.4, surface_harvested: 11476,  cane_production: 934578,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2015, region: 'OUEST',  tch: 99.9, surface_harvested: 3421,   cane_production: 341768,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2015, region: 'CENTRE', tch: 67.6, surface_harvested: 2183,   cane_production: 147491,  sugar_production: null,  extraction_rate: null,  tsh: null },
  // 2016
  { season: 2016, region: 'NORD',   tch: 78.1, surface_harvested: 6744,   cane_production: 526516,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2016, region: 'EST',    tch: 77.2, surface_harvested: 10383,  cane_production: 801981,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2016, region: 'SUD',    tch: 79.3, surface_harvested: 11115,  cane_production: 881457,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2016, region: 'OUEST',  tch: 85.7, surface_harvested: 3496,   cane_production: 299505,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2016, region: 'CENTRE', tch: 69.8, surface_harvested: 2236,   cane_production: 156094,  sugar_production: null,  extraction_rate: null,  tsh: null },
  // 2017
  { season: 2017, region: 'NORD',   tch: 83.7, surface_harvested: 6438,   cane_production: 539161,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2017, region: 'EST',    tch: 81.1, surface_harvested: 10030,  cane_production: 813674,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2017, region: 'SUD',    tch: 76.4, surface_harvested: 10721,  cane_production: 819252,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2017, region: 'OUEST',  tch: 85.8, surface_harvested: 3451,   cane_production: 296118,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2017, region: 'CENTRE', tch: 63.9, surface_harvested: 2159,   cane_production: 137980,  sugar_production: null,  extraction_rate: null,  tsh: null },
  // 2018
  { season: 2018, region: 'NORD',   tch: 72.4, surface_harvested: 6919,   cane_production: 500653,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2018, region: 'EST',    tch: 67.7, surface_harvested: 10404,  cane_production: 704057,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2018, region: 'SUD',    tch: 72.6, surface_harvested: 9959,   cane_production: 722642,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2018, region: 'OUEST',  tch: 80.2, surface_harvested: 3398,   cane_production: 272498,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2018, region: 'CENTRE', tch: 52.1, surface_harvested: 2207,   cane_production: 114972,  sugar_production: null,  extraction_rate: null,  tsh: null },
  // 2019
  { season: 2019, region: 'NORD',   tch: 80.2, surface_harvested: 6078,   cane_production: 487440,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2019, region: 'EST',    tch: 79.5, surface_harvested: 8891,   cane_production: 706843,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2019, region: 'SUD',    tch: 82.9, surface_harvested: 8294,   cane_production: 687758,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2019, region: 'OUEST',  tch: 89.1, surface_harvested: 3253,   cane_production: 289984,  sugar_production: null,  extraction_rate: null,  tsh: null },
  { season: 2019, region: 'CENTRE', tch: 64.8, surface_harvested: 1695,   cane_production: 109889,  sugar_production: null,  extraction_rate: null,  tsh: null },
  // 2020
  { season: 2020, region: 'NORD',   tch: 66.2, surface_harvested: 5813.6, cane_production: 384680,  sugar_production: 44278,  extraction_rate: 11.51, tsh: 7.6 },
  { season: 2020, region: 'EST',    tch: 67.2, surface_harvested: 8556.1, cane_production: 575266,  sugar_production: 57672,  extraction_rate: 10.03, tsh: 6.7 },
  { season: 2020, region: 'SUD',    tch: 67.0, surface_harvested: 8926,   cane_production: 597829,  sugar_production: 60610,  extraction_rate: 10.14, tsh: 6.8 },
  { season: 2020, region: 'OUEST',  tch: 64.8, surface_harvested: 3444.3, cane_production: 223309,  sugar_production: 24540,  extraction_rate: 10.99, tsh: 7.1 },
  { season: 2020, region: 'CENTRE', tch: 44.1, surface_harvested: 2036.8, cane_production: 89835,   sugar_production: 8544,   extraction_rate: 9.51,  tsh: 4.2 },
  // 2021
  { season: 2021, region: 'NORD',   tch: 70.1, surface_harvested: 5825.3, cane_production: 408287,  sugar_production: 40555,  extraction_rate: 9.93,  tsh: 7.0 },
  { season: 2021, region: 'EST',    tch: 72.3, surface_harvested: 7948.5, cane_production: 575048,  sugar_production: 52324,  extraction_rate: 9.10,  tsh: 6.7 },
  { season: 2021, region: 'SUD',    tch: 73.0, surface_harvested: 8428.6, cane_production: 615377,  sugar_production: 59787,  extraction_rate: 9.72,  tsh: 7.1 },
  { season: 2021, region: 'OUEST',  tch: 64.6, surface_harvested: 3399.7, cane_production: 219650,  sugar_production: 22964,  extraction_rate: 10.45, tsh: 6.8 },
  { season: 2021, region: 'CENTRE', tch: 51.0, surface_harvested: 1993.8, cane_production: 101728,  sugar_production: 8898,   extraction_rate: 9.04,  tsh: 4.6 },
  // 2022
  { season: 2022, region: 'NORD',   tch: 67.3, surface_harvested: 6156.2, cane_production: 414215,  sugar_production: 46305,  extraction_rate: 11.18, tsh: 7.5 },
  { season: 2022, region: 'EST',    tch: 63.3, surface_harvested: 7094.1, cane_production: 449256,  sugar_production: 44556,  extraction_rate: 9.92,  tsh: 6.3 },
  { season: 2022, region: 'SUD',    tch: 63.1, surface_harvested: 7789.5, cane_production: 491862,  sugar_production: 51472,  extraction_rate: 10.46, tsh: 6.6 },
  { season: 2022, region: 'OUEST',  tch: 69.9, surface_harvested: 3216.3, cane_production: 224945,  sugar_production: 24620,  extraction_rate: 10.94, tsh: 7.7 },
  { season: 2022, region: 'CENTRE', tch: 40.6, surface_harvested: 1723.3, cane_production: 69887,   sugar_production: 6393,   extraction_rate: 9.15,  tsh: 3.7 },
  // 2023
  { season: 2023, region: 'NORD',   tch: 72.1, surface_harvested: 6275,   cane_production: 452385,  sugar_production: 46104,  extraction_rate: 10.19, tsh: 7.3 },
  { season: 2023, region: 'EST',    tch: 74.0, surface_harvested: 7232.2, cane_production: 535296,  sugar_production: 52267,  extraction_rate: 9.76,  tsh: 7.2 },
  { season: 2023, region: 'SUD',    tch: 76.9, surface_harvested: 7118,   cane_production: 547389,  sugar_production: 53143,  extraction_rate: 9.71,  tsh: 7.5 },
  { season: 2023, region: 'OUEST',  tch: 69.9, surface_harvested: 2851.6, cane_production: 199340,  sugar_production: 20556,  extraction_rate: 10.31, tsh: 7.2 },
  { season: 2023, region: 'CENTRE', tch: 56.6, surface_harvested: 1555.1, cane_production: 88052,   sugar_production: 8306,   extraction_rate: 9.43,  tsh: 5.3 },
  // 2024
  { season: 2024, region: 'NORD',   tch: 74.5, surface_harvested: 5993.9, cane_production: 446353,  sugar_production: 49712,  extraction_rate: 11.14, tsh: 8.3 },
  { season: 2024, region: 'EST',    tch: 63.2, surface_harvested: 7530.5, cane_production: 476060,  sugar_production: 47149,  extraction_rate: 9.90,  tsh: 6.3 },
  { season: 2024, region: 'SUD',    tch: 73.2, surface_harvested: 7081.6, cane_production: 518426,  sugar_production: 53115,  extraction_rate: 10.25, tsh: 7.5 },
  { season: 2024, region: 'OUEST',  tch: 64.4, surface_harvested: 2582,   cane_production: 166375,  sugar_production: 18169,  extraction_rate: 10.92, tsh: 7.0 },
  { season: 2024, region: 'CENTRE', tch: 52.4, surface_harvested: 1521.4, cane_production: 79737,   sugar_production: 7507,   extraction_rate: 9.42,  tsh: 4.9 },
  // 2025 (most recent)
  { season: 2025, region: 'NORD',   tch: 74.0, surface_harvested: 5937.2, cane_production: 439562,  sugar_production: 43545,  extraction_rate: 9.91,  tsh: 7.3 },
  { season: 2025, region: 'EST',    tch: 71.5, surface_harvested: 7611.6, cane_production: 544402,  sugar_production: 50209,  extraction_rate: 9.22,  tsh: 6.6 },
  { season: 2025, region: 'SUD',    tch: 82.1, surface_harvested: 6840.1, cane_production: 561629,  sugar_production: 53626,  extraction_rate: 9.55,  tsh: 7.8 },
  { season: 2025, region: 'OUEST',  tch: 73.4, surface_harvested: 2635.6, cane_production: 193572,  sugar_production: 20198,  extraction_rate: 10.43, tsh: 7.7 },
  { season: 2025, region: 'CENTRE', tch: 55.6, surface_harvested: 1347.4, cane_production: 74879,   sugar_production: 6748,   extraction_rate: 9.01,  tsh: 5.0 },
]

// ── Current season predictions (placeholders until model is trained) ─
export const currentSeasonPredictions: { region: Region; predicted_tch: number; actual_tch: number }[] = [
  { region: 'NORD',   predicted_tch: 75.2, actual_tch: 74.0 },
  { region: 'EST',    predicted_tch: 70.8, actual_tch: 71.5 },
  { region: 'SUD',    predicted_tch: 81.4, actual_tch: 82.1 },
  { region: 'OUEST',  predicted_tch: 72.1, actual_tch: 73.4 },
  { region: 'CENTRE', predicted_tch: 54.9, actual_tch: 55.6 },
]

// ── Model metrics (placeholder until training complete) ──────
export const modelMetrics: ModelMetrics[] = [
  {
    name: 'RandomForest',
    rmse: 4.21,
    mae: 3.12,
    r2: 0.88,
    featureImportance: [
      { feature: 'NDVI Mean (Peak Season)',   importance: 0.31 },
      { feature: 'NDVI Cumulative',           importance: 0.26 },
      { feature: 'NDVI Max',                  importance: 0.20 },
      { feature: 'Season Year',               importance: 0.14 },
      { feature: 'Region',                    importance: 0.09 },
    ],
    predictions: [
      { actual: 72.4, predicted: 74.1 }, { actual: 77.5, predicted: 75.8 },
      { actual: 83.3, predicted: 81.2 }, { actual: 91.8, predicted: 89.5 },
      { actual: 74.5, predicted: 76.2 }, { actual: 83.4, predicted: 80.9 },
      { actual: 82.9, predicted: 84.3 }, { actual: 85.1, predicted: 83.7 },
      { actual: 66.2, predicted: 68.4 }, { actual: 67.2, predicted: 65.9 },
      { actual: 67.0, predicted: 69.1 }, { actual: 64.8, predicted: 66.2 },
      { actual: 44.1, predicted: 48.3 }, { actual: 72.1, predicted: 70.8 },
      { actual: 74.0, predicted: 75.1 }, { actual: 82.1, predicted: 79.6 },
    ],
  },
  {
    name: 'XGBoost',
    rmse: 3.78,
    mae: 2.91,
    r2: 0.93,
    featureImportance: [
      { feature: 'NDVI Mean (Peak Season)',   importance: 0.34 },
      { feature: 'NDVI Cumulative',           importance: 0.28 },
      { feature: 'NDVI Max',                  importance: 0.18 },
      { feature: 'Season Year',               importance: 0.12 },
      { feature: 'Region',                    importance: 0.08 },
    ],
    predictions: [
      { actual: 72.4, predicted: 73.2 }, { actual: 77.5, predicted: 76.8 },
      { actual: 83.3, predicted: 82.7 }, { actual: 91.8, predicted: 90.1 },
      { actual: 74.5, predicted: 75.3 }, { actual: 83.4, predicted: 82.1 },
      { actual: 82.9, predicted: 83.6 }, { actual: 85.1, predicted: 84.4 },
      { actual: 66.2, predicted: 67.3 }, { actual: 67.2, predicted: 66.8 },
      { actual: 67.0, predicted: 68.2 }, { actual: 64.8, predicted: 65.4 },
      { actual: 44.1, predicted: 46.7 }, { actual: 72.1, predicted: 71.4 },
      { actual: 74.0, predicted: 74.6 }, { actual: 82.1, predicted: 81.3 },
    ],
  },
]

// ── Sample weekly records (2025 season, illustrative) ────────
export const weeklyRecords: WeeklyRecord[] = [
  { week: 24, season: 2025, region: 'NORD',   surface_harvested: 380.2, cane_production: 28215, sugar_production: 2796, extraction_rate: 9.91, tch: 74.2, tsh: 7.4 },
  { week: 24, season: 2025, region: 'EST',    surface_harvested: 492.5, cane_production: 35208, sugar_production: 3245, extraction_rate: 9.22, tch: 71.5, tsh: 6.6 },
  { week: 24, season: 2025, region: 'SUD',    surface_harvested: 441.8, cane_production: 36244, sugar_production: 3462, extraction_rate: 9.55, tch: 82.0, tsh: 7.8 },
  { week: 24, season: 2025, region: 'OUEST',  surface_harvested: 170.1, cane_production: 12497, extraction_rate: 10.43, sugar_production: 1304, tch: 73.5, tsh: 7.7 },
  { week: 24, season: 2025, region: 'CENTRE', surface_harvested: 87.0,  cane_production: 4836,  sugar_production: 435,  extraction_rate: 9.01,  tch: 55.6, tsh: 5.0 },
  { week: 23, season: 2025, region: 'NORD',   surface_harvested: 362.5, cane_production: 26622, sugar_production: 2639, extraction_rate: 9.91, tch: 73.4, tsh: 7.3 },
  { week: 23, season: 2025, region: 'EST',    surface_harvested: 480.1, cane_production: 34327, sugar_production: 3164, extraction_rate: 9.22, tch: 71.5, tsh: 6.6 },
  { week: 23, season: 2025, region: 'SUD',    surface_harvested: 428.2, cane_production: 35153, sugar_production: 3357, extraction_rate: 9.55, tch: 82.1, tsh: 7.8 },
  { week: 23, season: 2025, region: 'OUEST',  surface_harvested: 162.5, cane_production: 11920, sugar_production: 1243, extraction_rate: 10.43, tch: 73.4, tsh: 7.7 },
  { week: 23, season: 2025, region: 'CENTRE', surface_harvested: 82.1,  cane_production: 4565,  sugar_production: 411,  extraction_rate: 9.01,  tch: 55.6, tsh: 5.0 },
  { week: 22, season: 2025, region: 'NORD',   surface_harvested: 340.0, cane_production: 24820, sugar_production: 2460, extraction_rate: 9.91, tch: 73.0, tsh: 7.2 },
  { week: 22, season: 2025, region: 'EST',    surface_harvested: 461.8, cane_production: 32918, sugar_production: 3035, extraction_rate: 9.22, tch: 71.3, tsh: 6.6 },
  { week: 22, season: 2025, region: 'SUD',    surface_harvested: 415.0, cane_production: 34032, sugar_production: 3250, extraction_rate: 9.55, tch: 82.0, tsh: 7.8 },
  { week: 22, season: 2025, region: 'OUEST',  surface_harvested: 155.2, cane_production: 11382, sugar_production: 1187, extraction_rate: 10.43, tch: 73.3, tsh: 7.7 },
  { week: 22, season: 2025, region: 'CENTRE', surface_harvested: 78.4,  cane_production: 4355,  sugar_production: 392,  extraction_rate: 9.01,  tch: 55.5, tsh: 5.0 },
]

// ── Helper: get TCH history for a single region ──────────────
export function getTchHistory(region: Region) {
  return historicalData
    .filter(d => d.region === region)
    .sort((a, b) => a.season - b.season)
    .map(d => ({ season: d.season, tch: d.tch }))
}

// ── Helper: get latest season data for all regions ───────────
export function getLatestSeasonData(season = 2025) {
  return historicalData.filter(d => d.season === season)
}

// ── Helper: national average TCH per season ─────────────────
export function getNationalAverageTch() {
  const seasons = [...new Set(historicalData.map(d => d.season))].sort()
  return seasons.map(s => {
    const rows = historicalData.filter(d => d.season === s)
    const avg = rows.reduce((sum, r) => sum + r.tch, 0) / rows.length
    return { season: s, tch: parseFloat(avg.toFixed(1)) }
  })
}
