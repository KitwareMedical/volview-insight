import { defineStore } from 'pinia';
import { useLocalStorage } from '@vueuse/core';
import { ref, computed } from 'vue';

export const useMedgemmaStore = defineStore('medgemma-store', () => {
  // Persistent state using localStorage
  const selectedModel = useLocalStorage<'medgemma' | 'monai-reasoning'>('medgemma-selected-model', 'medgemma');
  
  // Non-persistent state
  const analysisIdList = ref<string[]>([]);
  const analysisDone = ref<Record<string, boolean>>(Object.create(null));
  const analysisInput = ref<Record<string, Record<string, any>>>(Object.create(null));
  const analysisOutput = ref<Record<string, string | null>>(Object.create(null));
  
  // Define the initial state for vitals
  const vitals = ref<Record<string, any[]>>({
    heart_rate: [],
    respiratory_rate: [],
    temperature: [],
    systolic_bp: [],
    diastolic_bp: [],
    mean_arterial_pressure: [],
    spo2: [],
  });

  /**
   * Sets the current patient's vitals data in the store.
   * @param newVitals - An object where keys are vital names and values are arrays of FHIR Observations.
   */
  function setVitals(newVitals: Record<string, any[]>) {
    vitals.value = newVitals;
  }

  function addAnalysisId(id: string) {
    if (!analysisIdList.value.includes(id)) {
      analysisIdList.value.push(id);
    }
  }

  /**
   * Sets the input data for the analysis.
   * @param input - A dictionary where keys are strings and values are arrays of numbers.
   */
  function setAnalysisInput(id: string, input: Record<string, any>) {
    addAnalysisId(id);
    analysisInput.value[id] = input;
  }

  /**
   * Stores the result of the analysis and marks it as done.
   * @param result - A string representing the MedGemma model's output.
   */
  function setAnalysisResult(id: string, result: string) {
    analysisOutput.value[id] = result;
    analysisDone.value[id] = true;
  }

  /**
   * Resets the entire analysis state to its initial values.
   */
  function clearAnalysis(id: string) {
    if (id in analysisInput.value) {
      analysisInput.value[id] = {};
    }
    if (id in analysisOutput.value) {
      analysisOutput.value[id] = null;
    }
    if (id in analysisDone.value) {
      analysisDone.value[id] = false;
    }
  }

  /**
   * Sets the selected model for analysis.
   * @param model - The model to use for analysis ('medgemma' or 'monai-reasoning').
   */
  function setSelectedModel(model: 'medgemma' | 'monai-reasoning') {
    selectedModel.value = model;
  }

  return {
    // State
    selectedModel,
    analysisIdList,
    analysisDone,
    analysisInput,
    analysisOutput,
    vitals,
    
    // Actions
    setVitals,
    addAnalysisId,
    setAnalysisInput,
    setAnalysisResult,
    clearAnalysis,
    setSelectedModel,
  };
});
