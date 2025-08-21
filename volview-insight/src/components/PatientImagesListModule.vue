<script setup lang="ts">
import { computed } from 'vue';
import { storeToRefs } from 'pinia';

// --- Store Imports ---

// Manages data fetched directly from the DICOM server.
import { useDicomWebStore } from '../store/dicom-web/dicom-web-store';
import { useDicomMetaStore } from '@/src/store/dicom-web/dicom-meta-store';

// Manages app-wide state, including the currently selected patient (from FHIR).
import { useLocalFHIRStore } from '../store/local-fhir-store';

// --- Component Imports ---
import PatientDetails from './dicom-web/PatientDetails.vue';

// --- Store Instances ---

const dicomWebStore = useDicomWebStore();
const dicomMetaStore = useDicomMetaStore();
const localFHIRStore = useLocalFHIRStore();

// --- Reactive State from Stores ---

// Get a reactive reference to the patient selected from the FHIR store.
// We rename it to `selectedFHIRPatient` for maximum clarity on its origin.
const { selectedPatient: selectedFHIRPatient } = storeToRefs(localFHIRStore);

// --- Data Fetching ---

// Fetch all patient records from the DICOM server when the component is set up.
// This populates `dicomMetaStore` with the data we'll search through.
dicomWebStore.fetchDicomsOnce();

// --- Computed Properties ---

/**
 * Finds the detailed patient information from the DICOM store that corresponds
 * to the currently selected patient from the FHIR store.
 * This computed property is reactive and will update automatically if the
 * selected patient changes.
 * @returns { {key: string, name: string} | null }
 */
const selectedDicomPatient = computed(() => {
  // 1. Ensure a patient is selected in the app's global state.
  if (!selectedFHIRPatient.value) {
    return null;
  }

  // 2. Find the patient record from the DICOM server data whose PatientID
  //    matches the ID of the selected patient from the FHIR store.
  const foundDicomInfo = Object.values(dicomMetaStore.patientInfo).find(
    (dicomPatient) => dicomPatient.PatientID === selectedFHIRPatient.value?.id
  );

  // 3. If a match is found, return a clean object for the template to use.
  if (foundDicomInfo) {
    return {
      key: foundDicomInfo.PatientID,
      name: foundDicomInfo.PatientName,
    };
  }

  // 4. Return null if no matching patient is found in the DICOM data.
  return null;
});
</script>

<template>
  <!-- Make the container a vertical flexbox that fills available space -->
  <v-container fluid class="d-flex flex-column h-100">
    <v-alert
      v-if="dicomWebStore.message.length > 0"
      type="error"
      variant="tonal"
      border="start"
    >
      {{ dicomWebStore.message }}
    </v-alert>

    <div
      v-else-if="selectedFHIRPatient"
      class="d-flex flex-column flex-grow-1 min-h-0"
    >
      <div
        v-if="selectedDicomPatient"
        class="d-flex flex-column flex-grow-1 min-h-0"
      >
        <v-list-item class="px-1">
          <template #prepend>
            <v-icon>mdi-account</v-icon>
          </template>
          <v-list-item-title class="font-weight-medium">
            {{ selectedDicomPatient.name }}
          </v-list-item-title>
        </v-list-item>

        <v-list-subheader class="mt-4">
          Imaging Studies
        </v-list-subheader>

        <!-- This is the scrollable region -->
        <div class="pt-2 flex-grow-1 min-h-0 overflow-y-auto">
          <patient-details :patient-key="selectedDicomPatient.key" />
        </div>
      </div>

      <v-alert
        v-else
        type="info"
        variant="tonal"
        border="start"
        icon="mdi-image-search-outline"
      >
        No matching imaging studies found for the selected patient.
      </v-alert>
    </div>

    <v-alert
      v-else
      type="info"
      variant="tonal"
      border="start"
      icon="mdi-account-search-outline"
    >
      Please select a patient to view studies.
    </v-alert>
  </v-container>
</template>

<style scoped>
/* Most styling is handled by Vuetify, keeping this clean. */
.v-list-item-title {
  font-size: 1.125rem !important;
}

/* Ensures flex children can shrink and scroll correctly */
.min-h-0 {
  min-height: 0;
}
</style>

