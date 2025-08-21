import { defineStore } from 'pinia';
import { Ref, ref } from 'vue';
import { useLocalStorage } from '@vueuse/core';
import { useDatasetStore } from '@/src/store/datasets';

export const useLocalFHIRStore = defineStore('local-fhir-store', () => {
  const { VITE_LOCAL_FHIR_SERVER_NAME, VITE_LOCAL_FHIR_SERVER_URL, VITE_PATIENT_IDENTIFIER } = import.meta.env;

  // GUI display name
  const hostName = VITE_LOCAL_FHIR_SERVER_NAME
    ? ref(VITE_LOCAL_FHIR_SERVER_NAME)
    : useLocalStorage<string>('localFHIRServerHostName', '');

  // URL
  const hostURL = VITE_LOCAL_FHIR_SERVER_URL
    ? ref(VITE_LOCAL_FHIR_SERVER_URL)
    : useLocalStorage<string | null>('localFHIRServerHostURL', ''); // null if cleared by vuetify text input

  const identifierSystem = ref(VITE_PATIENT_IDENTIFIER);

  const selectedPatient = ref<{ id: string, name: string, resource_id: string } | null>(null);

  function setCurrentPatient(patient: { id: string, name: string, resource_id: string }) {
    let oldPatientId = selectedPatient.value?.id

    selectedPatient.value = patient;
    console.log('selectedPatient is: ', selectedPatient.value);

    // If the patient changes, remove the 'globally selected' volume
    const datasets = useDatasetStore();
    if (oldPatientId != selectedPatient.value?.id) {
      datasets.setPrimarySelection(null);
    }
  }

  function getCurrentPatient(): Ref<{ id: string, name: string, resource_id: string } | null> {
    return selectedPatient;
  }

  return {
    hostURL,
    hostName,
    selectedPatient,
    identifierSystem,
    setCurrentPatient,
    getCurrentPatient,
  };
});
