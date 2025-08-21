<script setup lang="ts">
import { computed, watch } from 'vue';
import { useLocalFHIRStore } from '../store/local-fhir-store';
import { usePythonAnalysisStore } from '../store/python-analysis-store';
import KitwareDatabasePointsToPersons from './icons/KitwareDatabasePointsToPersons.vue';
import KitwareMagnifyingGlass from './icons/KitwareMagnifyingGlass.vue';
import KitwareCodingGearSpinning from './icons/KitwareCodingGearSpinning.vue';
import { Line } from 'vue-chartjs';
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  LineController,      
  ScatterController,   
  LineElement,
  PointElement,
  LinearScale,
} from 'chart.js';
import type { ChartData, ScatterDataPoint } from 'chart.js';
import annotationPlugin from 'chartjs-plugin-annotation';

// Register Chart.js components and plugins
ChartJS.register(
  Title,
  Tooltip,
  Legend,
  LineController,      
  ScatterController,   
  LineElement,
  PointElement,
  LinearScale,
  annotationPlugin
);

const analysisSteps = [
  {
    iconComponent: KitwareDatabasePointsToPersons,
    title: 'Select a patient image',
    description: 'Choose the image you want to analyze from the patient view.',
  },
  {
    iconComponent: KitwareMagnifyingGlass,
    title: 'Go to the "Analysis" tab',
    description: 'Navigate to the Analysis tab to begin processing the image.',
  },
  {
    iconComponent: KitwareCodingGearSpinning,
    title: 'Perform the analysis to view results',
    description: 'Start the PyTorch analysis and view the AI-generated results here.',
  },
];

// Stores
const pythonAnalysisStore = usePythonAnalysisStore();
const localFHIRStore = useLocalFHIRStore();
const { getCurrentPatient } = localFHIRStore;
const currentPatient = computed(() => getCurrentPatient());

// Watch for changes to current patient
watch(currentPatient, () => {
  console.log("AnalyticsView patient changed update");
});

// Chart.js data and options
const chartData = computed(() => {
  const patientId = currentPatient.value?.value?.id;
  if (!patientId || !pythonAnalysisStore.analysisDone[patientId]) {
    return { datasets: [] };
  }

  const rawData: [number, number][] = pythonAnalysisStore.analysisInput[patientId];
  const analysisResult = pythonAnalysisStore.analysisOutput[patientId];
  if (!rawData || !analysisResult) {
      return { datasets: [] };
  }

  // Format scatter data for Chart.js: [x, y] -> {x, y}
  const scatterData: ScatterDataPoint[] = rawData.map(p => ({ x: p[0], y: p[1] }));

  const slope = analysisResult[0];
  const intercept = analysisResult[1];

  // Find min and max x values to draw the regression line
  const xVals = rawData.map(p => p[0]);
  const minX = Math.min(...xVals);
  const maxX = Math.max(...xVals);

  // Generate regression line points
  const regressionLineData = [
      { x: minX, y: slope * minX + intercept },
      { x: maxX, y: slope * maxX + intercept }
  ];

  return {
    datasets: [
      {
        type: 'scatter',
        label: 'Patient Metrics',
        data: scatterData,
        backgroundColor: 'rgba(99, 154, 255, 0.7)',
        borderColor: 'rgba(99, 154, 255, 1)',
      },
      {
        type: 'line',
        label: 'Trend',
        data: regressionLineData,
        borderColor: 'rgba(255, 99, 132, 1)',
        borderWidth: 2,
        fill: false,
        pointRadius: 0,
        tension: 0.1
      },
    ],
  } as ChartData<'line', (ScatterDataPoint | null)[]>;
});


const chartOptions = computed(() => {
    const patientId = currentPatient.value?.value?.id;
    if (!patientId) return undefined;

    const analysisResult = pythonAnalysisStore.analysisOutput[patientId];
    if (!analysisResult) return undefined;

    const slope = analysisResult[0];
    const intercept = analysisResult[1];
    const rSquared = analysisResult[2];

    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top' as const,
                labels: {
                  color: '#FFFFFF'
                }
            },
            title: {
                display: true,
                text: 'Total Lung Capacity (TLC) vs. Lung Field Area',
                font: {
                    size: 12,
                },
                color: '#FFFFFF',
                padding: {
                    bottom: 20
                }
            },
            tooltip: {
                mode: 'index' as const,
                intersect: false,
            },
            annotation: {
                annotations: {
                    statsLabel: {
                        type: 'label' as const,
                        content: [
                            `R-squared: ${rSquared.toFixed(3)}`,
                            `Slope (L/cm²): ${slope.toFixed(4)}`,
                            `Intercept (L): ${intercept.toFixed(2)}`
                        ],
                        color: 'white',
                        font: { size: 12, weight: 'bold' as 'bold' },
                        backgroundColor: 'rgba(0, 0, 0, 0.6)',
                        padding: 6,
                        borderRadius: 6,
                        xAdjust: 10,
                        yAdjust: 10,
                        position: {
                            x: 'start' as const,
                            y: 'start' as const,
                        },
                    },
                },
            },
        },
        scales: {
            x: {
                type: 'linear' as const,
                position: 'bottom' as const,
                title: {
                    display: true,
                    text: 'Lung Field Area (cm²)',
                    color: '#FFFFFF'
                },
                ticks: { color: '#B0B0B0' },
                grid: { color: 'rgba(255, 255, 255, 0.1)' }
            },
            y: {
                title: {
                    display: true,
                    text: 'TLC (L)',
                    color: '#FFFFFF'
                },
                ticks: { color: '#B0B0B0' },
                grid: { color: 'rgba(255, 255, 255, 0.1)' }
            },
        },
    };
});


defineOptions({
  name: 'AnalyticsView'
});
</script>

<template>
  <v-container
    v-if="currentPatient?.value && pythonAnalysisStore.analysisDone[currentPatient.value.id]"
    fluid
    class="pa-8 d-flex flex-column"
  >
    <h1 class="text-h4 font-weight-bold text-white mb-3 text-center">Patient Analysis</h1>
    <div class="chart-container">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </v-container>

  <v-container v-else class="fill-height pa-8" fluid>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="10" md="8" lg="7" xl="6">
        <v-card flat color="transparent" class="text-center">
          <h1 class="text-h4 font-weight-bold text-white mb-3">No Analysis Data</h1>
          <v-card-text class="text-body-1 text-medium-emphasis mb-10">
            You need to run an analysis on the patient data to see results here.
          </v-card-text>

          <v-list lines="two" bg-color="transparent" class="text-left">
            <v-list-item v-for="(step, i) in analysisSteps" :key="i" class="mb-4">
              <template #prepend>
                <div class="mr-5">
                  <component :is="step.iconComponent" />
                </div>
              </template>
              <v-list-item-title class="text-body-1 font-weight-medium text-white">
                {{ step.title }}
              </v-list-item-title>
              <v-list-item-subtitle class="text-medium-emphasis">
                {{ step.description }}
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.v-list-item {
  padding-inline-start: 0 !important;
  padding-inline-end: 0 !important;
}

.chart-container {
  position: relative;
  height: 100%;
  width: 100%;
}
</style>
