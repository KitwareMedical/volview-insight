<script setup lang="ts">
import { ref } from 'vue';
import { storeToRefs } from 'pinia';
import FHIR from 'fhirclient';
import { useLocalFHIRStore } from '../../store/local-fhir-store';

// Define a reusable type for the patient object.
type Patient = {
  id: string;
  name: string;
  resource_id: string;
};

// --- State Management ---

// Pinia store setup
const localFHIRStore = useLocalFHIRStore();
const { hostURL: localServerUrl, identifierSystem } = storeToRefs(localFHIRStore);

// Get a direct reactive reference to the store's current patient by calling the getter.
const activePatient = localFHIRStore.getCurrentPatient();

// Component reactive state
const patients = ref<Patient[]>([]);
const errorAlert = ref("");
const doLoginLoading = ref(false);

/**
 * In Vue, DOM manipulation should be handled reactively.
 * Use this ref with a v-if or v-show directive in your template
 * to hide the login button instead of using jQuery's .hide().
 * Example: <v-btn v-if="!isLoginComplete" @click="doLogin">Login</v-btn>
 */
const isLoginComplete = ref(false);


// --- Functions ---

/**
 * Fetches and processes patient data from the local FHIR server.
 */
async function login() {
  errorAlert.value = "";
  try {
    const client = FHIR.client({ serverUrl: localServerUrl.value });
    const response = await client.request(`Patient?identifier=${identifierSystem.value}%7C`);

    if (!response.entry?.length) {
      errorAlert.value = "No patient records found.";
      return;
    }

    // Map over patient entries, parse them, and filter out any invalid ones.
    const parsedPatients = response.entry
      .map((entry: any): Patient | null => {
        const resource = entry?.resource;
        if (!resource) return null;

        // Safely extract patient name using optional chaining.
        const nameObj = resource.name?.[0];
        const given = nameObj?.given?.[0] ?? "";
        const family = nameObj?.family ?? "";
        const name = `${given} ${family}`.trim() || "(No name found)";

        // Find the scoped ID and the internal resource ID.
        const id = resource.identifier?.find(
          (i: { system: string; }) => i.system === identifierSystem.value
        )?.value;
        const resource_id = resource.id;

        if (!id || !resource_id) {
          console.warn("Patient is missing a required identifier:", resource);
          return null;
        }

        return { id, name, resource_id };
      })
      .filter((p): p is Patient => p !== null); // Type guard to filter out nulls

    patients.value = parsedPatients;
    isLoginComplete.value = true; // Signal that login is done

  } catch (error) {
    console.error("FHIR login failed:", error);
    errorAlert.value = "Failed to connect to the local FHIR server.";
  } finally {
    doLoginLoading.value = false;
  }
}

/**
 * A wrapper function to set loading state before calling login.
 */
const doLogin = () => {
  doLoginLoading.value = true;
  login();
};

/**
 * Finds a patient by ID and sets them as the active patient in the component and the store.
 * @param {string} id - The scoped ID of the patient to set as active.
 */
const setPatient = (id: string) => {
  const patient = patients.value.find(p => p.id === id);
  if (patient) {
    // Calling the store's action will update the ref that our local `activePatient` points to.
    localFHIRStore.setCurrentPatient(patient);
  } else {
    console.warn("Could not set active patient: ID not found:", id);
  }
};
</script>

<template>
  <div class="ma-2">
    <v-list-subheader>Local FHIR Server</v-list-subheader>

    <v-card v-if="patients.length > 0" class="mx-auto overflow-y-auto" max-height="500px">
      <v-list>
        <v-list-item
          v-for="patient in patients"
          :key="patient.id"
          :active="activePatient?.id === patient.id"
          active-color="green"
          @click="setPatient(patient.id)"
        >
          <v-list-item-title>{{ patient.name }}</v-list-item-title>
          <v-list-item-subtitle>ID: {{ patient.id }}</v-list-item-subtitle>
        </v-list-item>
      </v-list>
    </v-card>

    <v-container v-else>
      <v-row>
        <v-col>
          <v-btn
            block
            class="primary"
            variant="tonal"
            prepend-icon="mdi-lan-connect"
            :loading="doLoginLoading"
            @click="doLogin"
          >
            Connect
          </v-btn>
        </v-col>
      </v-row>
    </v-container>

    <v-alert
      v-if="errorAlert"
      class="mt-4"
      type="warning"
      variant="tonal"
      transition="slide-y-transition"
      closable
      border
    >
      {{ errorAlert }}
    </v-alert>
  </div>
</template>

<style scoped>

.volume-card {
  padding: 8px;
  cursor: pointer;
}

</style>
