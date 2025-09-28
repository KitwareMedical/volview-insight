<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useLocalFHIRStore } from '../store/local-fhir-store';
import { useCurrentImage } from '@/src/composables/useCurrentImage';
import { useServerStore, ConnectionState } from '@/src/store/server';
import { getDataID, makeImageSelection } from '@/src/store/datasets';
import { useImageStore } from '@/src/store/datasets-images';
import { useDatasetStore } from '@/src/store/datasets';
import { useSegmentGroupStore } from '@/src/store/segmentGroups';
import { usePythonAnalysisStore } from '../store/python-analysis-store';

// --- loaded patient info --- //
const localFHIRStore = useLocalFHIRStore();
const { getCurrentPatient } = localFHIRStore;
const currentPatient = computed(() => getCurrentPatient());

// --- python analysis info --- //
const pythonAnalysisStore = usePythonAnalysisStore();

// --- loaded image --- //
const dataStore = useDatasetStore();
const imageStore = useImageStore();
const segmentGroupStore = useSegmentGroupStore();

// current slice for lung segmentation (in case image is 3D, lung seg must be
// 2D)
import useViewSliceStore from '@/src/store/view-configs/slicing';
const viewSliceStore = useViewSliceStore();
const { currentImageID } = useCurrentImage();
const viewIDToWatch = 'Axial'; // <-- We are targeting the Axial view which is set as the image viewer in ../../config.ts
const currentSlice = computed(() => {
  if (!currentImageID.value) return null; // Default value if no image
  
  const config = viewSliceStore.getConfig(viewIDToWatch, currentImageID.value);
  return config?.slice ?? null; // Return the slice or a default value
});
const hasCurrentImage = computed(() => !!currentImageID.value);

// --- backend volview --- //
const serverStore = useServerStore();
const { client } = serverStore;
const ready = computed(
  () => serverStore.connState === ConnectionState.Connected
);

// --- dummy analysis --- //
const exampleAnalysisLoading = ref(false);

const doExampleAnalysis = async () => {
  exampleAnalysisLoading.value = true;
  try {
    // Generate synthetic patient data simulating lung field area and TLC
    const samples: [number, number][] = [];
    const n = 20;

    // Linear model: TLC = a * (lung field area) + b + noise
    const a = 0.002; // liters per cm²
    const b = 1.5;   // baseline lung volume
    const noiseStdDev = 0.3; // realistic measurement noise

    for (let i = 0; i < n; i++) {
      // Simulate lung field area (in cm²) between 1200 and 2800
      const x = 1200 + Math.random() * 1600;

      // Simulate TLC with linear relationship + Gaussian noise
      const noise = noiseStdDev * (Math.sqrt(-2 * Math.log(Math.random())) * Math.cos(2 * Math.PI * Math.random()));
      const y = a * x + b + noise;

      samples.push([x, y]);
    }

    if (!currentPatient.value?.value?.id) {
      throw new Error("Patient ID is null or undefined");
    }
    pythonAnalysisStore.setAnalysisInput(currentPatient.value.value.id, samples);

    await client.call('exampleAnalysis', [currentPatient.value.value.id]);

    const output = pythonAnalysisStore.analysisOutput[currentPatient.value.value.id];
    console.log(output);
  } finally {
    exampleAnalysisLoading.value = false;
  }
};

// --- lung segmentation --- //
const lungSegmentationLoading = ref(false);

const doLungSegmentation = async () => {
  const currId = currentImageID.value;
  if (!currId) return;

  lungSegmentationLoading.value = true;
  try {
    await client.call('segmentLungs', [currId, currentSlice.value]);

    const seg_id = Object.keys(imageStore.metadata).find(id => imageStore.metadata[id].name === `${currId}_seg`);
    const segIdString = seg_id?.toString();
    const primarySelection = dataStore.primarySelection;
    if (primarySelection && segIdString) {
      segmentGroupStore.convertImageToLabelmap(
        makeImageSelection(segIdString),
        primarySelection
      );
    }
  } finally {
    lungSegmentationLoading.value = false;
  }
};

// watch current patient to nullify result if the patient changes
watch(currentPatient, () => console.log("Current patient changed!"));
</script>

<template>
  <div class="overflow-y-auto overflow-x-hidden ma-2 fill-height">
    <v-alert v-if="!ready" color="info">Not connected to the server.</v-alert>
    <v-divider />
    <v-list-subheader>Example Analysis</v-list-subheader>
    <div>
      <v-row>
        <v-col>
          <v-btn
            @click="doExampleAnalysis"
            :loading="exampleAnalysisLoading"
            :disabled="!ready || !currentPatient.value"
          >
            Perform Analysis
          </v-btn>
          <span v-if="!currentPatient.value" class="ml-4 body-2">
            No patient selected
          </span>
        </v-col>
      </v-row>
    </div>
    <v-list-subheader>Lung Segmentation</v-list-subheader>
    <div>
      <v-row>
        <v-col>
          <v-btn
            @click="doLungSegmentation"
            :loading="lungSegmentationLoading"
            :disabled="!ready || !hasCurrentImage"
          >
            Run Lung Segmentation
          </v-btn>
          <span v-if="!hasCurrentImage" class="ml-4 body-2">
            No image loaded
          </span>
        </v-col>
      </v-row>
    </div>
  </div>
</template>
