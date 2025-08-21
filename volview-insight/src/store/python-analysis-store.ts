import { defineStore } from 'pinia';

/**
 * Interface for the analysis store's state.
 */
interface State {
  analysisIdList: string[]; // list of analysis ids
  analysisDone: Record<string, Boolean>; // finished state is bool
  analysisInput: Record<string, [number, number][]>;  // inputs are arrays of 2d points
  analysisOutput: Record<string, [number, number, number] | null>; // outputs are m, b, and r-squared
}

export const usePythonAnalysisStore = defineStore('python-analysis-store', {
  /**
   * Defines the initial state of the store.
   */
  state: (): State => ({
    analysisIdList: [],
    analysisDone: Object.create(null),
    analysisInput: Object.create(null),
    analysisOutput: Object.create(null),
  }),

  /**
   * Actions to modify the store's state.
   */
  actions: {
    addAnalysisId(id: string) {
      if (!(id in this.analysisIdList)) {
        this.analysisIdList.push(id)
      }
    },

    /**
     * Sets the input data for the analysis.
     * @param input - An array of [number, number] tuples.
     */
    setAnalysisInput(id: string, input: [number, number][]) {
      this.addAnalysisId(id);
      this.analysisInput[id] = input;
    },

    /**
     * Stores the result of the analysis and marks it as done.
     * @param result - A tuple containing [slope, intercept, rSquared].
     */
    setAnalysisResult(id: string, result: [number, number, number]) {
      this.analysisOutput[id] = result;
      this.analysisDone[id] = true;
    },

    /**
     * Resets the entire analysis state to its initial values.
     */
    clearAnalysis(id: string) {
      if (id in this.analysisInput) {
        this.analysisInput[id] = [];
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
