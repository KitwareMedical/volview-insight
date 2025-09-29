import { defineStore } from 'pinia';

/**
 * Interface for the backend model store's state.
 */
interface State {
  selectedModel: string; // The currently selected backend model
  analysisIdList: string[]; // list of analysis ids
  analysisInput: Record<string, Record<string, any>>; // inputs are string-to-array-of-numbers dictionaries
  analysisOutput: Record<string, string | null>; // output is a string (e.g., the result from the selected model)
}

export const useBackendModelStore = defineStore('backend-model-store', {
  /**
   * Defines the initial state of the store.
   */
  state: (): State => ({
    selectedModel: 'medgemma', // Default model on initialization
    analysisIdList: [],
    analysisInput: Object.create(null),
    analysisOutput: Object.create(null),
  }),

  /**
   * Actions to modify the store's state.
   */
  actions: {
    /**
     * Sets the backend model to use for analysis.
     * @param model - The name of the model (e.g., 'medgemma', 'mrcxr1').
     */
    setModel(model: string) {
      this.selectedModel = model;
    },

    addAnalysisId(id: string) {
      if (!this.analysisIdList.includes(id)) {
        this.analysisIdList.push(id);
      }
    },

    /**
     * Sets the input data for the analysis.
     * @param patientId - The patient ID.
     * @param input - A dictionary where keys are strings and values are arrays of numbers.
     */
    setAnalysisInput(patientId: string, input: Record<string, any>) {
      this.analysisInput[patientId] = input;
    },

    /**
     * Sets the output result for the analysis.
     * @param patientId - The patient ID.
     * @param output - The analysis result as a string.
     */
    setAnalysisResult(patientId: string, output: string) {
      this.analysisOutput[patientId] = output;
    },

    /**
     * Clears analysis data for a specific patient.
     * @param patientId - The patient ID.
     */
    clearAnalysis(patientId: string) {
      delete this.analysisInput[patientId];
      delete this.analysisOutput[patientId];
    },

    /**
     * Clears all analysis data.
     */
    clearAllAnalyses() {
      this.analysisIdList = [];
      this.analysisInput = Object.create(null);
      this.analysisOutput = Object.create(null);
    },
  },
});
