import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useLocalStorage } from '@vueuse/core';

export const useLocalFHIRStore = defineStore('local-fhir-store', () => {
  const {
    VITE_LOCAL_FHIR_SERVER_NAME,
    VITE_LOCAL_FHIR_SERVER_URL,
    VITE_PATIENT_IDENTIFIER,
  } = import.meta.env;

  // GUI display name for the server
  const hostName = VITE_LOCAL_FHIR_SERVER_NAME
    ? ref(VITE_LOCAL_FHIR_SERVER_NAME)
    : useLocalStorage<string>('localFHIRServerHostName', '');

  // URL of the server
  const hostURL = VITE_LOCAL_FHIR_SERVER_URL
    ? ref(VITE_LOCAL_FHIR_SERVER_URL)
    : useLocalStorage<string | null>('localFHIRServerHostURL', '');

  // The identifier system used for patients
  const identifierSystem = ref(VITE_PATIENT_IDENTIFIER);

  return {
    hostURL,
    hostName,
    identifierSystem,
  };
});
