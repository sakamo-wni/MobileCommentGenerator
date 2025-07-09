import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
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
  expandedLocations: Record<string, boolean>;
  regeneratingStates: RegeneratingState;
  isRegeneratingSingle: boolean;
  generatedAt: string | null;
  
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
  setGeneratedAt: (timestamp: string | null) => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      immer((set) => ({
      // Initial state
      selectedLocation: null,
      selectedLocations: [],
      llmProvider: 'gemini',
      isBatchMode: false,
      generatedComment: null,
      batchResults: [],
      expandedLocations: {},
      regeneratingStates: {},
      isRegeneratingSingle: false,
      generatedAt: null,
      
      // Actions
      setSelectedLocation: (location) => set((state) => { state.selectedLocation = location; }),
      setSelectedLocations: (locations) => set((state) => { state.selectedLocations = locations; }),
      setLlmProvider: (provider) => set((state) => { state.llmProvider = provider; }),
      setIsBatchMode: (mode) => set((state) => { state.isBatchMode = mode; }),
      setGeneratedComment: (comment) => set((state) => { state.generatedComment = comment; }),
      setBatchResults: (results) => set((state) => {
        if (typeof results === 'function') {
          state.batchResults = results(state.batchResults);
        } else {
          state.batchResults = results;
        }
      }),
      toggleLocationExpanded: (location) => set((state) => {
        if (state.expandedLocations[location]) {
          delete state.expandedLocations[location];
        } else {
          state.expandedLocations[location] = true;
        }
      }),
      setRegeneratingState: (location, regenerating) => set((state) => {
        state.regeneratingStates[location] = regenerating;
      }),
      setIsRegeneratingSingle: (isRegenerating) => set((state) => { state.isRegeneratingSingle = isRegenerating; }),
      clearExpandedLocations: () => set((state) => { state.expandedLocations = {}; }),
      clearResults: () => set((state) => { 
        state.generatedComment = null;
        state.batchResults = [];
        state.expandedLocations = {};
        state.generatedAt = null;
      }),
      setGeneratedAt: (timestamp) => set((state) => { state.generatedAt = timestamp; })
    })),
      {
        name: 'mobile-comment-generator-store',
        partialize: (state) => ({
          llmProvider: state.llmProvider,
          isBatchMode: state.isBatchMode,
        })
      }
    ),
    {
      name: 'app-store',
    }
  )
);