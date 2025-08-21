<script setup lang="ts">
import { ref, computed } from 'vue';
import { storeToRefs } from 'pinia';
import MarkdownIt from 'markdown-it';
import { useCurrentImage } from '@/src/composables/useCurrentImage';
import { useLocalFHIRStore } from '../store/local-fhir-store';
import { useMedgemmaStore } from '../store/medgemma-store';
import { useServerStore, ConnectionState } from '@/src/store/server';

// --- Markdown Renderer Setup ---
// Initialize markdown-it. The `breaks: true` option converts '\n' in paragraphs into <br> tags.
const md = new MarkdownIt({ breaks: true });

// --- Store and Composables Setup ---
const localFHIRStore = useLocalFHIRStore();
const medgemmaStore = useMedgemmaStore();
const serverStore = useServerStore();

const { selectedPatient } = storeToRefs(localFHIRStore);
const { client } = serverStore;
const { currentImageID } = useCurrentImage();

// --- Component State ---
interface Message {
  id: number;
  text: string;
  sender: 'user' | 'bot';
}

const messages = ref<Message[]>([]);
const newMessage = ref('');
const isTyping = ref(false);

// --- Computed Properties ---
const ready = computed(() => serverStore.connState === ConnectionState.Connected);

// --- current slice being viewed in the Axial view, as it's a 2D view that slices a 3D image --- //
import useViewSliceStore from '@/src/store/view-configs/slicing';
const viewSliceStore = useViewSliceStore();
const viewIDToWatch = 'Axial'; // <-- We are targeting the Axial view which is set as the image viewer in ../../config.ts
const currentSlice = computed(() => {
  if (!currentImageID.value) return null; // Default value if no image
  
  const config = viewSliceStore.getConfig(viewIDToWatch, currentImageID.value);
  return config?.slice ?? null; // Return the slice or a default value
});

// --- Methods ---
const appendMessage = (text: string, sender: 'user' | 'bot') => {
  messages.value.push({ id: Date.now(), text, sender });
};

const sendMessage = async () => {
  const text = newMessage.value.trim();
  if (!text || isTyping.value) return;

  appendMessage(text, 'user');
  newMessage.value = '';
  isTyping.value = true;

  try {
    // Set up data inputs from the store
    if (!selectedPatient.value?.id) {
      throw new Error("No patient is selected.");
    }
    const image_id = currentImageID.value ?? null;

    // Define the payload. Note that the store contains vitals as FHIR Observation
    // resources, so we must extract them.
    const payload = {
        prompt: text,
        heart_rate: medgemmaStore.vitals.heart_rate
            ?.map(obs => obs?.valueQuantity?.value)
            .filter(v => v != null) ?? [],
        respiratory_rate: medgemmaStore.vitals.respiratory_rate
            ?.map(obs => obs?.valueQuantity?.value)
            .filter(v => v != null) ?? [],
        spo2: medgemmaStore.vitals.spo2
            ?.map(obs => obs?.valueQuantity?.value)
            .filter(v => v != null) ?? [],
    };

    medgemmaStore.setAnalysisInput(selectedPatient.value.id, payload);

    // Invoke the RPC call
    await client.call('medgemmaAnalysis', [selectedPatient.value.id, image_id, currentSlice.value]);

    // Get the data outputs from the store
    const botResponse = medgemmaStore.analysisOutput[selectedPatient.value.id];
    if (!botResponse || typeof botResponse !== 'string') {
        throw new Error("Received an invalid response from the server.");
    }

    appendMessage(botResponse, 'bot');
  } catch (error) {
    console.error("Error calling medgemmaAnalysis:", error);
    appendMessage("Sorry, an error occurred while processing your request. Please try again.", 'bot');
  } finally {
    isTyping.value = false;
  }
};
</script>

<template>
  <v-container fluid class="fill-height pa-0">
    <v-card v-if="selectedPatient" class="chat-card">
      <v-card-text class="chat-log">
        <div
          v-for="message in messages"
          :key="message.id"
          :class="['d-flex', message.sender === 'user' ? 'justify-end' : 'justify-start']"
          class="mb-4"
        >
          <div :class="['message-bubble', `message-${message.sender}`]">
            <div v-if="message.sender === 'bot'" v-html="md.render(message.text)"></div>
            <div v-else class="message-text-user">{{ message.text }}</div>
          </div>
        </div>
      </v-card-text>

      <v-progress-linear
        v-if="isTyping"
        indeterminate
        color="primary"
      ></v-progress-linear>

      <v-card-actions class="pa-4">
        <v-text-field
          v-model="newMessage"
          @keydown.enter="sendMessage"
          @keydown.stop
          :disabled="isTyping"
          label="Type your message..."
          variant="solo"
          hide-details
          clearable
        >
          <template #append-inner>
            <v-btn
              @click="sendMessage"
              :disabled="isTyping || !newMessage"
              icon="mdi-send"
              variant="text"
              color="primary"
            ></v-btn>
          </template>
        </v-text-field>
      </v-card-actions>
    </v-card>

    <v-alert
      v-else
      type="info"
      variant="tonal"
      border="start"
      icon="mdi-account-search-outline"
    >
      Please select a patient to begin a chat session.
    </v-alert>
  </v-container>
</template>

<style scoped>
.chat-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

.chat-log {
  flex-grow: 1;
  overflow-y: auto;
  padding: 16px;
}

.message-bubble {
  padding: 10px 16px;
  border-radius: 18px;
  max-width: 70%;
  line-height: 1.5;
  word-wrap: break-word;
}

.message-user {
  background-color: rgb(var(--v-theme-primary));
  color: rgb(var(--v-theme-on-primary));
  border-bottom-right-radius: 4px;
}

.message-bot {
  background-color: rgb(var(--v-theme-surface-variant));
  color: rgb(var(--v-theme-on-surface-variant));
  border-bottom-left-radius: 4px;
}

.message-text-user {
  /* This ensures user-typed newlines are respected */
  white-space: pre-wrap;
}

/* Styles for rendered markdown content from the bot.
  ':deep()' is used to apply styles to the v-html content,
  which is not processed by Vue's scoped styles otherwise.
*/
.message-bot :deep(p) {
  margin-bottom: 0.5em;
}
.message-bot :deep(p:last-child) {
  margin-bottom: 0;
}
.message-bot :deep(ul),
.message-bot :deep(ol) {
  padding-left: 20px;
  margin-bottom: 0.5em;
}
.message-bot :deep(li) {
  margin-bottom: 0.25em;
}
.message-bot :deep(strong) {
  font-weight: 600;
}
</style>
