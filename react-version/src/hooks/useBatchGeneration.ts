import { useState, useCallback } from 'react';
import type { Location, BatchResult } from '@mobile-comment-generator/shared';
import { BATCH_CONFIG } from '../../../src/config/constants';
import { getLocationInfo } from '../constants/regions';

interface UseBatchGenerationProps {
  generateComment: (location: Location, options: any) => Promise<any>;
  llmProvider: 'openai' | 'gemini' | 'anthropic';
}

interface RegeneratingState {
  [location: string]: boolean;
}

export function useBatchGeneration({ generateComment, llmProvider }: UseBatchGenerationProps) {
  const [batchResults, setBatchResults] = useState<BatchResult[]>([]);
  const [regeneratingStates, setRegeneratingStates] = useState<RegeneratingState>({});

  const handleBatchGenerate = useCallback(async (selectedLocations: string[]) => {
    // Initialize all results with loading state
    const placeholderResults: BatchResult[] = selectedLocations.map(location => ({
      location,
      success: false,
      loading: true,
      comment: null,
      metadata: null,
      error: null
    }));
    setBatchResults(placeholderResults);

    // Process all locations with controlled concurrency
    for (let i = 0; i < selectedLocations.length; i += BATCH_CONFIG.CONCURRENT_LIMIT) {
      const chunk = selectedLocations.slice(i, i + BATCH_CONFIG.CONCURRENT_LIMIT);
      
      const chunkPromises = chunk.map(async (locationName: string, chunkIdx: number) => {
        const globalIdx = i + chunkIdx;
        try {
          const locationInfo = getLocationInfo(locationName);
          const locationObj: Location = {
            id: locationName,
            name: locationName,
            prefecture: locationInfo.prefecture,
            region: locationInfo.region
          };

          const result = await generateComment(locationObj, {
            llmProvider,
          });

          // Update state immediately for progressive display
          const successResult = {
            success: true,
            location: locationName,
            comment: result.comment,
            metadata: result.metadata,
            weather: result.weather,
            adviceComment: result.adviceComment,
            loading: false
          };
          
          setBatchResults(prev => {
            const newResults = [...prev];
            newResults[globalIdx] = successResult;
            return newResults;
          });

          return successResult;
        } catch (error) {
          const errorResult = {
            success: false,
            location: locationName,
            error: error instanceof Error ? error.message : 'コメント生成に失敗しました',
            loading: false
          };
          
          setBatchResults(prev => {
            const newResults = [...prev];
            newResults[globalIdx] = errorResult;
            return newResults;
          });
          
          return errorResult;
        }
      });

      // Wait for all requests in the chunk to complete before processing next chunk
      await Promise.allSettled(chunkPromises);
    }
  }, [generateComment, llmProvider]);

  const handleRegenerateBatch = useCallback(async (locationName: string) => {
    setRegeneratingStates(prev => ({ ...prev, [locationName]: true }));

    try {
      const locationInfo = getLocationInfo(locationName);
      const locationObj: Location = {
        id: locationName,
        name: locationName,
        prefecture: locationInfo.prefecture,
        region: locationInfo.region
      };

      const result = await generateComment(locationObj, {
        llmProvider,
        excludePrevious: true,
      });

      const newResult: BatchResult = {
        success: true,
        location: locationName,
        comment: result.comment,
        metadata: result.metadata,
        weather: result.weather,
        adviceComment: result.adviceComment
      };

      setBatchResults(prev =>
        prev.map(item =>
          item.location === locationName ? newResult : item
        )
      );
    } catch (error) {
      const errorResult: BatchResult = {
        success: false,
        location: locationName,
        error: error instanceof Error ? error.message : 'コメント再生成に失敗しました'
      };

      setBatchResults(prev =>
        prev.map(item =>
          item.location === locationName ? errorResult : item
        )
      );
    } finally {
      setRegeneratingStates(prev => {
        const newState = { ...prev };
        delete newState[locationName];
        return newState;
      });
    }
  }, [generateComment, llmProvider]);

  return {
    batchResults,
    regeneratingStates,
    handleBatchGenerate,
    handleRegenerateBatch,
    setBatchResults
  };
}