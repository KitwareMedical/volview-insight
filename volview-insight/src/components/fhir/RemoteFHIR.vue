<script setup lang="ts">
import { ref } from 'vue';
import FHIR from 'fhirclient';
import type { Patient } from '@medplum/fhirtypes';

// Reactive state
const errorAlert = ref("");
const doLoginLoading = ref(false);
const patientInfo = ref<Patient | null>(null);

/**
 * Handles the OAuth message after a successful login.
 * @param {any} msg - The OAuth message data from the popup window.
 */
function processOAuthMessage(msg: any) {
  sessionStorage[msg.storage.key] = msg.storage.value;
  window.history.pushState({}, "FHIR Patient", `/?code=${msg.code}&state=${msg.state}`);

  FHIR.oauth2.ready()
    .then(client => client.request("Patient"))
    .then(info => {
      // Assuming the first entry is the patient
      patientInfo.value = info?.entry[0]?.resource;
    })
    .catch(err => {
      console.error("Error fetching patient data:", err);
      errorAlert.value = "Failed to fetch patient data from the remote EHR.";
    });
}

/**
 * Opens a popup window to initiate the FHIR OAuth2 login flow.
 */
function login() {
  const width = 780;
  const height = 550;
  const left = (window.screen.width - width) / 2;
  const top = (window.screen.height - height) / 2 - 20;

  const windowFeatures = {
    width,
    height,
    left,
    top: Math.max(0, top), // Ensure top isn't negative
    titlebar: 'no',
    location: 'no',
    popup: 'yes',
  };

  const featuresString = Object.entries(windowFeatures)
    .map(([key, value]) => `${key}=${value}`)
    .join(',');

  const baseUrl = window.location.origin;
  // This is a Vite-specific way to resolve assets in the public directory
  const loginUrl = `${baseUrl}/volview-insight/fhir-login/launch.html?iss=https://fhir-ehr-code.cerner.com/dstu2/ec2458f2-1e24-41c8-b71b-0e701af7583d`;

  const loginWindow = window.open(loginUrl, '_blank', featuresString);

  const handleMessage = (event: MessageEvent) => {
    const oauthMessage = event.data;
    if (oauthMessage?.url && oauthMessage.code && oauthMessage.state && oauthMessage.storage) {
      loginWindow?.close();
      processOAuthMessage(oauthMessage);
      // Clean up the event listener once we have the message
      window.removeEventListener("message", handleMessage);
    }
  };

  window.addEventListener("message", handleMessage, false);
}

/**
 * A wrapper function for the login process that handles loading states and errors.
 */
const doLogin = async () => {
  doLoginLoading.value = true;
  errorAlert.value = ""; // Clear previous errors
  try {
    login();
  } catch (err) {
    console.error("Login initiation failed:", err);
    errorAlert.value = "Failed to open the login window. Please ensure popups are enabled.";
  } finally {
    // Note: Loading state might need to be managed differently,
    // as the process is asynchronous and involves user interaction in a popup.
    // We set it to false here, but the actual "loading" continues until the user logs in.
    doLoginLoading.value = false;
  }
};
</script>

<template>
  <div class="ma-2">
    <v-list-subheader>Remote FHIR Server</v-list-subheader>

    <div id="remote-ptable" class="mt-2" style="font-size: 0.8rem" hidden>
      <div class="text-overline">Current Patient</div>
      <v-divider class="mb-2" />
      <v-table density="compact">
        <tbody>
          <tr>
            <td class="font-weight-bold pr-4">ID</td>
            <td id="remote-pid"></td>
          </tr>
          <tr>
            <td class="font-weight-bold pr-4">Name</td>
            <td id="remote-pname"></td>
          </tr>
          <tr>
            <td class="font-weight-bold pr-4">DOB</td>
            <td id="remote-pdob"></td>
          </tr>
          <tr>
            <td class="font-weight-bold pr-4">Gender</td>
            <td id="remote-pgender"></td>
          </tr>
          <tr>
            <td class="font-weight-bold pr-4">Address</td>
            <td id="remote-paddr"></td>
          </tr>
        </tbody>
      </v-table>
    </div>

    <v-container>
      <v-row>
        <v-col>
          <v-btn
            block
            variant="tonal"
            :loading="doLoginLoading"
            @click="doLogin"
          >
            Login
          </v-btn>
        </v-col>
      </v-row>
    </v-container>

    <v-alert
      v-if="errorAlert.length > 0"
      class="mt-4"
      type="warning"
      variant="tonal"
      transition="slide-y-transition"
      border="start"
      density="compact"
    >
      {{ errorAlert }}
    </v-alert>
  </div>
</template>
