import { useState, useCallback } from 'react';

export function useUIState() {
  const [expandedLocations, setExpandedLocations] = useState<Set<string>>(new Set());

  const toggleLocationExpanded = useCallback((location: string) => {
    setExpandedLocations(prev => {
      const newSet = new Set(prev);
      if (newSet.has(location)) {
        newSet.delete(location);
      } else {
        newSet.add(location);
      }
      return newSet;
    });
  }, []);

  const handleCopyComment = useCallback((text: string) => {
    navigator.clipboard?.writeText(text);
    console.log('Copied:', text);
  }, []);

  const clearExpandedLocations = useCallback(() => {
    setExpandedLocations(new Set());
  }, []);

  return {
    expandedLocations,
    toggleLocationExpanded,
    handleCopyComment,
    clearExpandedLocations
  };
}