<script setup lang="ts">
import { watch, ref, nextTick } from 'vue';
import FHIR from 'fhirclient';
import type { Bundle } from '@medplum/fhirtypes';
import { storeToRefs } from 'pinia';
import { useLocalFHIRStore } from '../store/local-fhir-store';
import { Line } from 'vue-chartjs';
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  TimeScale,
} from 'chart.js';
import type { ChartData, ScatterDataPoint } from 'chart.js';
import 'chartjs-adapter-date-fns';

// Constants
const VITAL_SIGN_CODES: Record<string, string> = {
 
  '220045': 'heart_rate',
  '220210': 'respiratory_rate',
  '223761': 'temperature',
  '220179': 'systolic_bp',
  '220180': 'diastolic_bp',
  '220052': 'mean_arterial_pressure',
  '220277': 'spo2', 
};

const VITAL_SIGN_LABELS: Record<string, string> = {
  heart_rate: 'Heart Rate',
  respiratory_rate: 'Resp. Rate',
  temperature: 'Temp.',
  systolic_bp: 'Sys. BP',
  diastolic_bp: 'Dia. BP',
  mean_arterial_pressure: 'Avg Arterial Press.',
  spo2: 'SpO2',
};

const VITALS_COLOR_MAP: Record<string, string> = {
  heart_rate: '#E57373',         
  respiratory_rate: '#FFB74D',   
  temperature: '#64B5F6',        
  systolic_bp: '#81C784',        
  diastolic_bp: '#BA68C8',       
  mean_arterial_pressure: '#B0B0B0',
  spo2: '#4DB6AC',              
};

// ChartJS setup
ChartJS.register(
  Title,
  Tooltip,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  TimeScale
);

// Refs
const localFHIRStore = useLocalFHIRStore();
const { getCurrentPatient } = localFHIRStore;
const { hostURL: localServerUrl } = storeToRefs(localFHIRStore);
const currentPatient = getCurrentPatient();
const fhirClient = FHIR.client({
  serverUrl: localServerUrl.value
});

const observations = ref<any[]>([]);
const conditions = ref<any[]>([]);
const timeSeriesChartData = ref<ChartData<'line', ScatterDataPoint[]>>({
  datasets: [],
});
const vitals = ref<Record<string, any[]>>({
  heart_rate: [],
  respiratory_rate: [],
  temperature: [],
  systolic_bp: [],
  diastolic_bp: [],
  mean_arterial_pressure: [],
  spo2: [],
});
const vitalStats = ref<Record<string, { mean: number | null; stddev: number | null }>>({
  heart_rate: { mean: null, stddev: null },
  respiratory_rate: { mean: null, stddev: null },
  temperature: { mean: null, stddev: null },
  systolic_bp: { mean: null, stddev: null },
  diastolic_bp: { mean: null, stddev: null },
  mean_arterial_pressure: { mean: null, stddev: null },
  spo2: { mean: null, stddev: null },
});
const selectedVital = ref<string>('heart_rate');

const chartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      mode: 'index',
      intersect: false,
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
      titleColor: '#FFFFFF',
      bodyColor: '#FFFFFF',
      borderColor: 'rgba(255, 255, 255, 0.2)',
      borderWidth: 1,
    },
  },
  scales: {
    x: {
      type: 'time',
      time: { 
        tooltipFormat: 'MM/dd/yyyy HH:mm',
        displayFormats: {
          hour: 'MM/dd/yyyy HH:mm',
          minute: 'MM/dd/yyyy HH:mm',
          second: 'MM/dd/yyyy HH:mm:ss'
        }
      },
      title: {
        display: true,
        text: 'Time',
        color: '#FFFFFF',
        font: {
          size: 14
        }
      },
      ticks: {
        color: '#B0B0B0',
      },
      grid: {
        color: 'rgba(255, 255, 255, 0.1)',
      },
    },
    y: {
      title: {
        display: true,
        text: 'Value',
        color: '#FFFFFF',
        font: {
          size: 14
        }
      },
      ticks: {
        color: '#B0B0B0',
      },
      grid: {
        color: 'rgba(255, 255, 255, 0.1)',
      },
    },
  },
});

// Watch the vitals ref for changes and update the backend model store
import { useBackendModelStore } from '../store/backend-model-store';
const backendModelStore = useBackendModelStore();
watch(vitals, (newVitals) => {
  backendModelStore.setVitals(newVitals);
}, { deep: true }); // Use { deep: true } to watch for changes inside the object

/**
 * Computes the mean and standard deviation for each vital sign.
 * 
 * For each vital sign key in the provided vitals object, this function extracts
 * all numeric values and calculates the mean and sample standard deviation.
 * If fewer than 2 valid numeric values are found, the result will contain
 * `null` for both mean and stddev.
 * 
 * @param vitalsData - A record of vital sign observations, keyed by vital name.
 * @returns A record of statistics (mean and stddev) for each vital sign.
 */
function computeVitalStats(
  vitalsData: Record<string, any[]>
): Record<string, { mean: number | null; stddev: number | null }> {
  const stats: Record<string, { mean: number | null; stddev: number | null }> = {};

  for (const [key, obsList] of Object.entries(vitalsData)) {
    const values: number[] = obsList
      .map((obs) => obs?.valueQuantity?.value)
      .filter((v: number | undefined): v is number => typeof v === 'number');

    if (values.length < 2) {
      stats[key] = { mean: null, stddev: null };
      continue;
    }

    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const variance =
      values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (values.length - 1);
    const stddev = Math.sqrt(variance);

    stats[key] = { mean, stddev };
  }

  return stats;
}

/**
 * Extracts and groups FHIR Observation resources representing common vital signs,
 * based on known vital sign codes, then sorts each group by the resource's 
 * last updated timestamp in descending order (most recent first).
 *
 * @param observations - An array of FHIR Observation resources.
 * @returns A record object where each key is a vital sign name (e.g., "heart_rate"),
 *          and the value is an array of corresponding Observation resources,
 *          sorted by `.meta.lastUpdated` in descending order.
 */
function extractAndSortVitalSignsObservations(observations: any[]): Record<string, any[]> {
  const vitalSigns: Record<string, any[]> = {
    heart_rate: [],
    respiratory_rate: [],
    temperature: [],
    systolic_bp: [],
    diastolic_bp: [],
    mean_arterial_pressure: [],
    spo2: [],
  };

  for (const obs of observations) {
    const coding = obs?.code?.coding?.[0];
    const code = coding?.code;
    if (!code) continue;

    const vitalKey = VITAL_SIGN_CODES[code];
    if (vitalKey) {
      vitalSigns[vitalKey].push(obs);
    }
  }

 
  for (const key in vitalSigns) {
    vitalSigns[key].sort((a, b) => {
      const dateA = new Date(a.meta?.lastUpdated || 0).getTime();
      const dateB = new Date(b.meta?.lastUpdated || 0).getTime();
      return dateB - dateA;
    });
  }

  return vitalSigns;
}

/**
 * Transforms grouped vital sign observations into a Chart.js-compatible dataset format.
 * 
 * This function processes a record of vital sign arrays and extracts time series data
 * (x = timestamp, y = numeric value) from each observation. The output is structured 
 * as a `{ datasets: [...] }` object, which aligns with the expected input for the 
 * `vue-chartjs` <Line> component and Chart.js more broadly.
 * 
 * @param vitalData - An array of observation resources for a single vital sign.
 * @param color - The color for the chart line and points.
 * @param label - The display label for the dataset.
 * @returns A Chart.js data object with a single dataset.
 */
function computeTimeSeriesChartData(
  vitalData: any[],
  color: string,
  label: string
): ChartData<'line', ScatterDataPoint[]> {
  const points = vitalData
    .map((resource) => {
      const dateStr =
        resource?.meta?.lastUpdated ||
        resource?.effectiveDateTime ||
        resource?.issued;
      const x = new Date(dateStr);
      const y = resource?.valueQuantity?.value;
      return y != null && !isNaN(x.getTime()) ? { x: x.getTime(), y } : null;
    })
    .filter(Boolean) as { x: number; y: number }[];

  const dataset = {
    label: label,
    data: points,
    borderColor: color,
    backgroundColor: color,
    fill: false,
    tension: 0,
    borderWidth: 2,
    pointRadius: 2,
    pointHoverRadius: 6,
  };

  return { datasets: [dataset] };
}

/**
 * Updates the chart to display the currently selected vital sign.
 */
function updateChartData() {
  const vitalKey = selectedVital.value;
  const vitalData = vitals.value[vitalKey];

  if (vitalData && vitalData.length > 0) {
    const color = VITALS_COLOR_MAP[vitalKey];
    const label = VITAL_SIGN_LABELS[vitalKey];
    timeSeriesChartData.value = computeTimeSeriesChartData(vitalData, color, label);

    const newUnit = vitalData[0]?.valueQuantity?.unit || 'Value';

    // Create a new options object to ensure reactivity
    chartOptions.value = {
      ...chartOptions.value,
      scales: {
        ...chartOptions.value.scales,
        y: {
          ...chartOptions.value.scales.y,
          title: {
            ...chartOptions.value.scales.y.title,
            text: newUnit, // Set the new unit here
          },
        },
      },
    };

  } else {
    timeSeriesChartData.value = { datasets: [] };

    // Also update options here to reset the label
    chartOptions.value = {
      ...chartOptions.value,
      scales: {
        ...chartOptions.value.scales,
        y: {
          ...chartOptions.value.scales.y,
          title: {
            ...chartOptions.value.scales.y.title,
            text: 'Value', // Reset to default
          },
        },
      },
    };
  }
}

/**
 * Fetches all FHIR resources of a given type associated with a specific patient.
 * 
 * This function handles paginated responses by following `next` links in the bundle.
 * It also adjusts URLs to match the local server's host and port, which may differ
 * from those returned by the FHIR server (e.g., when running in Docker).
 * 
 * @param resourceType - The FHIR resource type to fetch (e.g., "Observation").
 * @param patientResourceId - The ID of the patient whose resources should be retrieved.
 * @returns A Promise that resolves to an array of FHIR resources.
 */
async function fetchAllFHIRResourcesForPatient(
  resourceType: string,
  patientResourceId: string
): Promise<any[]> {
  const allResources: any[] = [];
  let nextUrl: string | null = `${resourceType}?subject=Patient/${patientResourceId}`;

  const baseUrl = new URL(localServerUrl.value);

  while (nextUrl) {
    const bundle: Bundle = await fhirClient.request(nextUrl);

    if (bundle.entry) {
      allResources.push(...bundle.entry.map((e: any) => e.resource));
    }

    const nextLink = bundle.link?.find((link: any) => link.relation === 'next');
    if (nextLink?.url) {
      const rawNextUrl = new URL(nextLink.url);
      rawNextUrl.protocol = baseUrl.protocol;
      rawNextUrl.host = baseUrl.host;
      nextUrl = rawNextUrl.toString();
    } else {
      nextUrl = null;
    }
  }

  return allResources;
}

async function fetchChartDataForPatient() {
  const patientResourceId = currentPatient.value?.resource_id;
  if (!patientResourceId) return;

  console.log('Fetching chart data for patient:', currentPatient.value);

  try {
    observations.value = await fetchAllFHIRResourcesForPatient('Observation', patientResourceId);
    conditions.value = await fetchAllFHIRResourcesForPatient('Condition', patientResourceId);
    vitals.value = extractAndSortVitalSignsObservations(observations.value);
    vitalStats.value = computeVitalStats(vitals.value);

    await nextTick();
    updateChartData();

    console.log("Observations:", observations.value);
    console.log("Conditions:", conditions.value);
    console.log("Vitals Summary:", vitals);
    console.log("timeSeriesChartData Summary:", timeSeriesChartData);
    console.log("vitalStats Summary:", vitalStats);
  } catch (error) {
    console.error("Failed to fetch patient chart data:", error);
  }
}

// Watchers
watch(currentPatient, fetchChartDataForPatient, { immediate: true });
watch(selectedVital, updateChartData);

defineOptions({
  name: 'ChartView'
});
</script>

<template>
  <v-container class="pa-8 height-zero" fluid>
    <v-row justify="center" class="mb-4" dense>
      <v-btn-toggle v-model="selectedVital" class="flex-wrap" divided mandatory>
        <v-btn
          v-for="(label, key) in VITAL_SIGN_LABELS"
          :key="key"
          :value="key"
					size="x-small"
        >
          {{ label }}
        </v-btn>
      </v-btn-toggle>
    </v-row>

    <v-row :class="{ 'chart-row-expanded': timeSeriesChartData.datasets.length && timeSeriesChartData.datasets[0].data.length }">
      <v-col cols="12">
        <div v-if="timeSeriesChartData.datasets.length && timeSeriesChartData.datasets[0].data.length">
          <Line
            class="chart-row-expanded"
            :data="timeSeriesChartData"
            :options="chartOptions"
          />
        </div>

        <div v-else class="text-center">
          <v-card class="no-data-card d-inline-block" flat>
            <v-card-text class="text-body-1 text-medium-emphasis">
              Insufficient data for {{ VITAL_SIGN_LABELS[selectedVital] }} to create a graph.
            </v-card-text>
          </v-card>
        </div>
      </v-col>
    </v-row>

    <v-row>
      <v-col>
        <v-card flat color="transparent">
          <v-card-title class="text-h6 font-weight-bold text-white text-center">
            Vital Statistics Summary
          </v-card-title>
          <v-list lines="two" bg-color="transparent">
            <v-list-item v-for="(stat, key) in vitalStats" :key="key">
              <v-list-item-title class="text-body-1 font-weight-medium text-white">
                {{ VITAL_SIGN_LABELS[key] }}
              </v-list-item-title>
              <v-list-item-subtitle class="text-medium-emphasis">
                <span v-if="stat.mean !== null && stat.stddev !== null">
                  Mean: {{ stat.mean.toFixed(2) }}, Std Dev: {{ stat.stddev.toFixed(2) }}
                </span>
                <span v-else>No data</span>
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="6">
        <v-card flat color="transparent">
          <v-card-title class="text-h6 font-weight-bold text-white text-center">
            Observations
          </v-card-title>
          <v-list lines="two" bg-color="transparent">
            <v-list-item v-for="obs in observations" :key="obs.id">
              <v-list-item-title class="text-body-1 font-weight-medium text-white">
                {{ obs.code?.coding?.[0]?.display || "Unnamed Observation" }}
              </v-list-item-title>
              <v-list-item-subtitle class="text-medium-emphasis">
                {{ obs.valueQuantity?.value }} {{ obs.valueQuantity?.unit }}
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card flat color="transparent">
          <v-card-title class="text-h6 font-weight-bold text-white text-center">
            Conditions
          </v-card-title>
          <v-list lines="two" bg-color="transparent">
            <v-list-item v-for="cond in conditions" :key="cond.id">
              <v-list-item-title class="text-body-1 font-weight-medium text-white">
                {{ cond.code?.coding?.[0]?.display || "Unnamed Condition" }}
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.height-zero {
  height: 0;
}

.chart-row-expanded {
  height: 350px;
}

.v-btn-toggle.flex-wrap {
  flex-wrap: wrap;
  justify-content: center;
}

.no-data-card {
  border: 1px solid white !important;
  background-color: transparent !important;
}

.v-list-item {
  padding-inline-start: 0 !important;
  padding-inline-end: 0 !important;
}
</style>
