import { useState, useCallback } from 'react';
import type { GenerateSettings, GeneratedComment, Location } from '@mobile-comment-generator/shared';
import { createWeatherCommentComposable } from '@mobile-comment-generator/shared';

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const composable = createWeatherCommentComposable();

  const generateComment = useCallback(async (
    location: Location,
    settings: Omit<GenerateSettings, 'location'>
  ): Promise<GeneratedComment> => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await composable.generateComment(location, settings);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'コメント生成に失敗しました';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [composable]);

  const getHistory = useCallback(async (limit?: number): Promise<GeneratedComment[]> => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await composable.getHistory(limit);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '履歴の取得に失敗しました';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [composable]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    loading,
    error,
    generateComment,
    getHistory,
    clearError,
  };
};