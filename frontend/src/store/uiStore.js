import { create } from 'zustand'

export const useUiStore = create((set) => ({
  agenceFiltre: null,
  setAgenceFiltre: (agenceFiltre) => set({ agenceFiltre }),
}))
