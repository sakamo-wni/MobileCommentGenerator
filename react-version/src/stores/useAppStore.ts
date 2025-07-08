import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { Location, GeneratedComment, BatchResult } from '@mobile-comment-generator/shared';

interface RegeneratingState {
  [location: string]: boolean;
}

interface AppState {
  // Location state
  selectedLocation: Location | null;
  selectedLocations: string[];
  
  // Settings state
  llmProvider: 'openai' | 'gemini' | 'anthropic';
  isBatchMode: boolean;
  
  // Results state
  generatedComment: GeneratedComment | null;
  batchResults: BatchResult[];
  
  // UI state
  expandedLocations: Set<string>;
  regeneratingStates: RegeneratingState;
  isRegeneratingSingle: boolean;
  
  // Actions
  setSelectedLocation: (location: Location | null) => void;
  setSelectedLocations: (locations: string[]) => void;
  setLlmProvider: (provider: 'openai' | 'gemini' | 'anthropic') => void;
  setIsBatchMode: (mode: boolean) => void;
  setGeneratedComment: (comment: GeneratedComment | null) => void;
  setBatchResults: (results: BatchResult[] | ((prev: BatchResult[]) => BatchResult[])) => void;
  toggleLocationExpanded: (location: string) => void;
  setRegeneratingState: (location: string, state: boolean) => void;
  setIsRegeneratingSingle: (state: boolean) => void;
  clearExpandedLocations: () => void;
  clearResults: () => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    (set) => ({
      // Initial state
      selectedLocation: null,
      selectedLocations: [],
      llmProvider: 'gemini',
      isBatchMode: false,
      generatedComment: null,
      batchResults: [],
      expandedLocations: new Set(),
      regeneratingStates: {},
      isRegeneratingSingle: false,
      
      // Actions
      setSelectedLocation: (location) => set({ selectedLocation: location }),
      setSelectedLocations: (locations) => set({ selectedLocations: locations }),
      setLlmProvider: (provider) => set({ llmProvider: provider }),
      setIsBatchMode: (mode) => set({ isBatchMode: mode }),
      setGeneratedComment: (comment) => set({ generatedComment: comment }),
      setBatchResults: (results) => set((state) => ({
        batchResults: typeof results === 'function' ? results(state.batchResults) : results
      })),
      toggleLocationExpanded: (location) => set((state) => {
        const newSet = new Set(state.expandedLocations);
        if (newSet.has(location)) {
          newSet.delete(location);
        } else {
          newSet.add(location);
        }
        return { expandedLocations: newSet };
      }),
      setRegeneratingState: (location, regenerating) => set((state) => {
        if (regenerating) {
          return {
            regeneratingStates: { ...state.regeneratingStates, [location]: true }
          };
        } else {
          const newStates = { ...state.regeneratingStates };
          delete newStates[location];
          return { regeneratingStates: newStates };
        }
      }),
      setIsRegeneratingSingle: (state) => set({ isRegeneratingSingle: state }),
      clearExpandedLocations: () => set({ expandedLocations: new Set() }),
      clearResults: () => set({ 
        generatedComment: null, 
        batchResults: [],
        expandedLocations: new Set()
      })
    }),
    {
      name: 'app-store',
    }
  )
);