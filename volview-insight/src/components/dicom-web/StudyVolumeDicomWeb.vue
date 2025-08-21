<script setup lang="ts">
import { computed, onMounted, reactive, watchEffect, ref } from 'vue';
import { useDicomMetaStore } from '@/src/store/dicom-web/dicom-meta-store';
import {
  useDicomWebStore,
  type VolumeProgress,
} from '../../store/dicom-web/dicom-web-store';
import { formatBytes } from '@/src/utils';
import PersistentOverlay from '@/src/components/PersistentOverlay.vue';

// --- Props ---
const props = defineProps<{
  /** An array of volume keys to be displayed. */
  volumeKeys: string[];
}>();

// --- State and Stores ---
const dicomMetaStore = useDicomMetaStore();
const dicomWebStore = useDicomWebStore();
const thumbnailCache = reactive<Record<string, string>>({});
const lastSelectedKey = ref<string | null>(null);

// --- Initial Data Fetching ---
onMounted(() => {
  dicomWebStore.fetchVolumesMeta(props.volumeKeys);
});

// --- Helper Functions ---
const percentDone = (progress: VolumeProgress): number => {
  if (!progress || progress.total === 0) return 0;
  return Math.round((100 * progress.loaded) / progress.total);
};

const isLoadingState = (s?: string) => s === 'Pending' || s === 'Active';

const isCardDisabled = (volumeKey: string, state?: string) => {
  // Disable if this volume is loading
  if (isLoadingState(state)) return true;

  // While something is loading, disable the same card we just clicked
  if (isAnyVolumeLoading.value && lastSelectedKey.value === volumeKey) return true;

  return false;
};

// --- Computed Properties ---
const availableVolumeKeys = computed(() => {
  const { volumeInstances, instanceInfo } = dicomMetaStore;
  return props.volumeKeys.filter((key) => {
    const firstInstance = volumeInstances[key]?.[0];
    return firstInstance && instanceInfo[firstInstance];
  });
});

const volumes = computed(() => {
  const { volumeInfo, volumeInstances, instanceInfo } = dicomMetaStore;
  return availableVolumeKeys.value.map((key) => {
    const firstInstance = instanceInfo[volumeInstances[key][0]];
    const { Rows: rows, Columns: columns } = firstInstance;
    const info = volumeInfo[key];
    const progress = dicomWebStore.volumes[key];
    return {
      key,
      info,
      dimensions: `${columns}x${rows}x${info.NumberOfSlices}`,
      progress: {
        ...progress,
        percent: percentDone(progress),
      },
    };
  });
});

const isAnyVolumeLoading = computed(() =>
  volumes.value.some((v) => isLoadingState(v.progress?.state))
);

// --- Watchers ---
watchEffect(() => {
  availableVolumeKeys.value
    .filter((key) => !(key in thumbnailCache))
    .forEach(async (key) => {
      const thumb = await dicomWebStore.fetchVolumeThumbnail(key);
      if (thumb) {
        thumbnailCache[key] = thumb;
      }
    });
});

// --- Methods ---
function downloadDicom(volumeKey: string) {
  lastSelectedKey.value = volumeKey;
  dicomWebStore.downloadVolume(volumeKey);
}
</script>

<template>
  <v-container fluid class="pa-0">
    <div class="volume-list">
      <v-card
        v-for="volume in volumes"
        :key="volume.key"
        variant="outlined"
        class="volume-card"
        :title="volume.info.SeriesDescription"
        :disabled="isCardDisabled(volume.key, volume.progress?.state)"
        :ripple="!isCardDisabled(volume.key, volume.progress?.state)"
        @click="downloadDicom(volume.key)"
      >
        <div class="thumbnail-container pa-2">
          <v-img cover height="150" :src="thumbnailCache[volume.key]">
            <persistent-overlay>
              <div class="text-caption">
                {{ volume.dimensions }}
                <v-tooltip location="top" activator="parent">
                  Width x Height x Frames
                </v-tooltip>
              </div>
            </persistent-overlay>
            <persistent-overlay
              v-if="isLoadingState(volume.progress?.state)"
            >
              <div class="d-flex flex-column fill-height ma-0">
                <v-row
                  no-gutters
                  justify="center"
                  align="center"
                  class="flex-grow-1"
                >
                  <v-progress-circular
                    color="white"
                    :indeterminate="
                      volume.progress.percent === 0 &&
                      volume.progress.state === 'Pending'
                    "
                    :model-value="volume.progress.percent"
                  >
                    <span
                      v-if="volume.progress.percent > 0"
                      class="text-caption"
                    >
                      {{ volume.progress.percent }}
                    </span>
                  </v-progress-circular>
                </v-row>
                <v-row no-gutters justify="center" align="end">
                  <div
                    v-if="volume.progress.loaded > 0"
                    class="mb-1 text-caption"
                  >
                    {{ formatBytes(volume.progress.loaded) }}
                  </div>
                </v-row>
              </div>
            </persistent-overlay>
          </v-img>
        </div>

        <v-card-text class="text-caption text-center series-desc py-2">
          <div class="text-truncate">
            {{ volume.info.SeriesDescription || '(no series description)' }}
          </div>
        </v-card-text>
      </v-card>
    </div>
  </v-container>
</template>

<style scoped>
.volume-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 8px;
  padding: 8px;
}

.volume-card {
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.thumbnail-container {
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.series-desc {
  line-height: 1.2;
}
</style>

