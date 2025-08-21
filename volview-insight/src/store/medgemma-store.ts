import { defineStore } from 'pinia';

/**
 * Interface for the MedGemma store's state.
 */
interface State {
  analysisIdList: string[]; // list of analysis ids
  analysisDone: Record<string, boolean>; // finished state is bool
  analysisInput: Record<string, Record<string, any>>;  // inputs are string-to-array-of-numbers dictionaries
  analysisOutput: Record<string, string | null>; // output is a string (e.g., the result of MedGemma)
  // Add vitals to the state interface
  vitals: Record<string, any[]>;
}

export const useMedgemmaStore = defineStore('medgemma-store', {
  /**
   * Defines the initial state of the store.
   */
  state: (): State => ({
    analysisIdList: [],
    analysisDone: Object.create(null),
    analysisInput: Object.create(null),
    analysisOutput: Object.create(null),

    // Define the initial state for vitals
    vitals: {
      heart_rate: [],
      respiratory_rate: [],
      temperature: [],
      systolic_bp: [],
      diastolic_bp: [],
      mean_arterial_pressure: [],
      spo2: [],
    },
  }),

  /**
   * Actions to modify the store's state.
   */
  actions: {
    /**
     * Sets the current patient's vitals data in the store.
     * @param newVitals - An object where keys are vital names and values are arrays of FHIR Observations.
     */
    setVitals(newVitals: Record<string, any[]>) {
      this.vitals = newVitals;
    },

    addAnalysisId(id: string) {
      if (!this.analysisIdList.includes(id)) {
        this.analysisIdList.push(id);
      }
    },

    /**
     * Sets the input data for the analysis.
     * @param input - A dictionary where keys are strings and values are arrays of numbers.
     */
    setAnalysisInput(id: string, input: Record<string, any>) {
      this.addAnalysisId(id);
      this.analysisInput[id] = input;
    },

    /**
     * Stores the result of the analysis and marks it as done.
     * @param result - A string representing the MedGemma model's output.
     */
    setAnalysisResult(id: string, result: string) {
      this.analysisOutput[id] = result;
      this.analysisDone[id] = true;
    },

    /**
     * Resets the entire analysis state to its initial values.
     */
    clearAnalysis(id: string) {
      if (id in this.analysisInput) {
        this.analysisInput[id] = {};
      }
      if (id in this.analysisOutput) {
        this.analysisOutput[id] = null;
      }
      if (id in this.analysisDone) {
        this.analysisDone[id] = false;
      }
    },
  },
});
