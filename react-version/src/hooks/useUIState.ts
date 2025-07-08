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

  const handleCopyComment = useCallback(async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      console.log('Copied:', text);
      // Success is handled by the UI components that show copy feedback
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
      // Error feedback could be handled by a global toast/notification system
    }
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