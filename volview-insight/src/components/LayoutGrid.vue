<script setup lang="ts">
import { computed, type Component } from 'vue';
import { storeToRefs } from 'pinia';
import VtkTwoView from '@/src/components/VtkTwoView.vue';
import VtkObliqueView from '@/src/components/VtkObliqueView.vue';
import VtkObliqueThreeView from '@/src/components/VtkObliqueThreeView.vue';
import VtkThreeView from '@/src/components/VtkThreeView.vue';
import AnalyticsView from './AnalyticsView.vue';
import ChartView from './ChartView.vue';
import { Layout, LayoutDirection } from '@/src/types/layout';
import { useViewStore } from '@/src/store/views';
import { ViewType } from '../types/views';

// --- Component Definitions ---
// A mapping from view type names to their corresponding component implementations.
const TYPE_TO_COMPONENT: Record<ViewType, Component> = {
  '2D': VtkTwoView,
  '3D': VtkThreeView,
  Analytics: AnalyticsView,
  Chart: ChartView,
  Oblique: VtkObliqueView,
  Oblique3D: VtkObliqueThreeView,
};

// --- Props ---
// Define the component's props using the defineProps macro.
// The 'layout' prop is required for the component to function.
const props = defineProps<{
  layout: Layout;
}>();

// --- State Management ---
// Initialize the view store and get reactive references to its state.
const viewStore = useViewStore();
const { viewSpecs } = storeToRefs(viewStore);

// --- Computed Properties ---
// Determines the flex-direction class based on the layout direction.
const flexFlow = computed(() => {
  return props.layout.direction === LayoutDirection.H
    ? 'flex-column'
    : 'flex-row';
});

// Processes the layout items to prepare them for rendering.
// It maps layout definitions to either nested layouts or view components.
const items = computed(() => {
  const viewIDToSpecs = viewSpecs.value;
  return props.layout.items.map((item) => {
    // If the item is a string, it's a view ID.
    // We look up its spec and prepare it for dynamic component rendering.
    if (typeof item === 'string') {
      const spec = viewIDToSpecs[item];
      return {
        type: 'view',
        id: item,
        component: TYPE_TO_COMPONENT[spec.viewType],
        props: spec.props,
      };
    }
    // Otherwise, it's a nested layout object.
    return {
      type: 'layout',
      ...item,
    };
  });
});

// Note: In <script setup>, this component can recursively refer to itself
// via its filename, so an explicit name definition is not required.
</script>

<template>
  <div
    class="layout-container flex-equal"
    :class="flexFlow"
    data-testid="layout-grid"
  >
    <!-- Loop through each item in the processed layout -->
    <div v-for="(item, i) in items" :key="i" class="d-flex flex-equal" style="min-height:0">
      <!-- If the item is a layout, render the component recursively -->
      <layout-grid v-if="item.type === 'layout'" :layout="(item as Layout)" />
      <!-- Otherwise, render the specified view component dynamically -->
      <div v-else class="layout-item">
        <component
          :is="item.component"
          :key="item.id"
          :id="item.id"
          v-bind="item.props"
        />
      </div>
    </div>
  </div>
</template>

<!-- The styles remain unchanged -->
<style scoped src="@/src/components/styles/utils.css"></style>

<style scoped>
.layout-container {
  display: flex;
  flex-direction: column;
}

.layout-item {
  display: flex;
  flex: 1;
  border: 1px solid #222;
  overflow: auto;
}
</style>
