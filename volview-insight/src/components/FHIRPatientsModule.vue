<script setup lang="ts">
import { ref } from 'vue';
import RemoteFHIR from './fhir/RemoteFHIR.vue';
import LocalFHIR from './fhir/LocalFHIR.vue';

const isRemote = ref(false); // by default we use local

</script>

<template>
  <v-container fluid class="pa-0">
    <v-sheet class="pa-4 d-flex align-center" rounded="0">
      <v-switch
        v-model="isRemote"
        hide-details
        inset
        color="primary"
        class="ma-0"
        :label="`Source: ${isRemote ? 'Remote' : 'Local'}`"
      />
    </v-sheet>

    <v-divider />

    <div>
      <remote-FHIR v-if="isRemote" />
      <local-FHIR v-else />
    </div>
  </v-container>
</template>
