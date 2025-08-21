<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useDicomMetaStore } from '@/src/store/dicom-web/dicom-meta-store';
import { useDicomWebStore } from '../../store/dicom-web/dicom-web-store';
import StudyVolumeDicomWeb from './StudyVolumeDicomWeb.vue';
import { useLocalFHIRStore } from '../../store/local-fhir-store';

// --- State Management ---

const localFHIRStore = useLocalFHIRStore();
const dicomStore = useDicomMetaStore();
const dicomWebStore = useDicomWebStore();

// Get a reactive reference to the patient from the FHIR store.
const { selectedPatient: selectedFHIRPatient } = storeToRefs(localFHIRStore);

// --- Component State ---

// The key for the currently selected patient.
const selectedPatientId = computed(() => selectedFHIRPatient.value?.id);

// Tracks the loading state of the patient's metadata.
const isFetching = ref(true);

// Controls which expansion panels are open.
const panels = ref<string[]>([]);

// --- Data Fetching ---

// Fetch patient metadata and update the loading state.
watch(
  selectedPatientId,
  (patientId) => {
    if (patientId) {
      isFetching.value = true;
      dicomWebStore.fetchPatientMeta(patientId).finally(() => {
        isFetching.value = false;
      });
    }
  },
  { immediate: true }
);

// --- Computed Properties ---

// Computes a structured list of studies for the current patient.
const studies = computed(() => {
  if (!selectedPatientId.value) {
    return [];
  }
  const { patientStudies, studyInfo, studyVolumes } = dicomStore;
  return patientStudies[selectedPatientId.value]?.map((studyKey) => {
    const info = studyInfo[studyKey];
    return {
      ...info,
      key: studyKey,
      // Provide a fallback title if StudyDescription is missing.
      title: info.StudyDescription || info.StudyDate || info.StudyInstanceUID,
      // Get and sort the volume keys associated with the study.
      volumeKeys: studyVolumes[studyKey]?.sort() ?? [],
    };
  });
});

// Extracts just the keys from the computed studies list.
const studyKeys = computed(() => studies.value?.map(({ key }) => key) ?? []);

// --- Watchers ---

// Watches for changes in study keys and automatically expands panels
// if they are linked to a specific study or series.
watch(
  studyKeys,
  (keys) => {
    if (dicomWebStore.linkedToStudyOrSeries && keys) {
      // Use a Set to avoid duplicate panel entries.
      panels.value = Array.from(new Set([...panels.value, ...keys]));
    }
  },
  { immediate: true } // Run the watcher immediately on component load.
);
</script>

<template>
  <v-expansion-panels
    id="patient-data-studies"
    v-model="panels"
    accordion
    multiple
  >
    <v-expansion-panel
      v-for="study in studies"
      :key="study.StudyInstanceUID"
      :value="study.StudyInstanceUID"
      class="patient-data-study-panel"
    >
      <v-expansion-panel-title
        color="#1976fa0a"
        class="pl-3 no-select"
        :title="study.StudyDate"
      >
        <div class="study-header">
          <div class="study-header-title">
            <v-icon class="mb-2">mdi-folder-table</v-icon>
            <div class="ml-2 overflow-hidden text-no-wrap">
              <div class="text-subtitle-2 text-truncate" :title="study.title">
                {{ study.title }}
              </div>
              <div
                v-if="study.StudyDescription"
                class="text-caption text-truncate"
              >
                {{ study.StudyDate }}
              </div>
            </div>
          </div>

          <div class="d-flex flex-column align-center justify-end mx-2">
            <div class="d-flex flex-row align-center mr-2">
              <v-progress-circular
                v-if="isFetching"
                indeterminate
                :size="20"
                :width="2"
                class="mr-2"
              >
              </v-progress-circular>
              <v-icon size="small">mdi-folder-open</v-icon>
              <span class="text-caption text--secondary text-no-wrap">
                : {{ study.volumeKeys.length }}
              </span>
              <v-tooltip location="bottom" activator="parent">
                Total series in study
              </v-tooltip>
            </div>
          </div>
        </div>
      </v-expansion-panel-title>
      <v-expansion-panel-text>
        <study-volume-dicom-web :volume-keys="study.volumeKeys" />
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<style>
#patient-data-studies .v-expansion-panel::before {
  box-shadow: none;
}
</style>

<style scoped>
.study-header {
  display: flex;
  flex-flow: row;
  align-items: center;
  width: calc(100% - 24px);
}

.study-header-title {
  display: flex;
  flex-flow: row;
  align-items: center;
  flex-grow: 1;
  /* used to ensure that the text can truncate */
  min-width: 0;
}
</style>
