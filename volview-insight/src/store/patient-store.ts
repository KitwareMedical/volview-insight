import { defineStore } from 'pinia';
import { useDatasetStore } from '@/src/store/datasets';

/**
 * Interface for a patient record.
 */
interface Patient {
  id: string;
  name: string;
  resource_id: string;
}

/**
 * Interface for patient vitals.
 */
interface Vitals {
  heart_rate: any[];
  respiratory_rate: any[];
  temperature: any[];
  systolic_bp: any[];
  diastolic_bp: any[];
  mean_arterial_pressure: any[];
  spo2: any[];
}

/**
 * Interface for the patient store's state.
 */
interface State {
  selectedPatient: Patient | null;
  vitals: Vitals;
}

const getInitialVitals = (): Vitals => ({
  heart_rate: [],
  respiratory_rate: [],
  temperature: [],
  systolic_bp: [],
  diastolic_bp: [],
  mean_arterial_pressure: [],
  spo2: [],
});

export const usePatientStore = defineStore('patient-store', {
  /**
   * Defines the initial state of the store.
   */
  state: (): State => ({
    selectedPatient: null,
    vitals: getInitialVitals(),
  }),

  /**
   * Actions to modify the store's state.
   */
  actions: {
    /**
     * Sets the currently active patient.
     * If the patient changes, it clears any primary volume selection.
     * @param patient - The patient object to set as current.
     */
    setCurrentPatient(patient: Patient) {
      const oldPatientId = this.selectedPatient?.id;
      this.selectedPatient = patient;

      // If the patient is different, clear the primary volume selection
      if (oldPatientId !== patient.id) {
        const datasets = useDatasetStore();
        datasets.setPrimarySelection(null);
      }
    },

    /**
     * Updates the vitals for the current patient.
     * @param newVitals - The new vitals data.
     */
    setVitals(newVitals: Vitals) {
      this.vitals = newVitals;
    },

    /**
     * Clears the current patient data and vitals.
     */
    clearPatient() {
      this.selectedPatient = null;
      this.vitals = getInitialVitals();
      const datasets = useDatasetStore();
      datasets.setPrimarySelection(null);
    },
  },
});
