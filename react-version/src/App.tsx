import React, { useCallback, useMemo } from 'react';
import { Cloud, Sparkles, Sun, Moon, ChevronDown, ChevronUp, Copy, CheckCircle } from 'lucide-react';
import type { Location, GeneratedComment, BatchResult } from '@mobile-comment-generator/shared';
import { LocationSelection } from './components/LocationSelection';
import { GenerateSettings } from './components/GenerateSettings';
import { GeneratedCommentDisplay } from './components/GeneratedComment';
import { WeatherDataDisplay } from './components/WeatherData';
import { BatchResultItem } from './components/BatchResultItem';
import { useApi } from './hooks/useApi';
import { useTheme } from './hooks/useTheme';
import { useAppStore } from './stores/useAppStore';
import { REGIONS } from './constants/regions';
import { BATCH_CONFIG } from '../../src/config/constants';

// Constants for batch mode
const WARN_BATCH_LOCATIONS = 20;

// Helper function to find location info from regions data
function getLocationInfo(locationName: string): { prefecture: string; region: string } {
  for (const [regionName, prefectures] of Object.entries(REGIONS)) {
    for (const [prefName, locations] of Object.entries(prefectures)) {
      if (locations.includes(locationName)) {
        return { prefecture: prefName, region: regionName };
      }
    }
  }
  // Fallback values if not found
  return { prefecture: '不明', region: '不明' };
}

function App() {
  // Get state from Zustand store
  const selectedLocation = useAppStore((state) => state.selectedLocation);
  const selectedLocations = useAppStore((state) => state.selectedLocations);
  const llmProvider = useAppStore((state) => state.llmProvider);
  const isBatchMode = useAppStore((state) => state.isBatchMode);
  const generatedComment = useAppStore((state) => state.generatedComment);
  const batchResults = useAppStore((state) => state.batchResults);
  const expandedLocations = useAppStore((state) => state.expandedLocations);
  const regeneratingStates = useAppStore((state) => state.regeneratingStates);
  const isRegeneratingSingle = useAppStore((state) => state.isRegeneratingSingle);

  // Get actions from Zustand store
  const setSelectedLocation = useAppStore((state) => state.setSelectedLocation);
  const setSelectedLocations = useAppStore((state) => state.setSelectedLocations);
  const setLlmProvider = useAppStore((state) => state.setLlmProvider);
  const setIsBatchMode = useAppStore((state) => state.setIsBatchMode);
  const setGeneratedComment = useAppStore((state) => state.setGeneratedComment);
  const setBatchResults = useAppStore((state) => state.setBatchResults);
  const toggleLocationExpanded = useAppStore((state) => state.toggleLocationExpanded);
  
  // Memoized toggle location expanded callback
  const handleToggleLocationExpanded = useCallback((location: string) => {
    toggleLocationExpanded(location);
  }, [toggleLocationExpanded]);
  const setRegeneratingState = useAppStore((state) => state.setRegeneratingState);
  const setIsRegeneratingSingle = useAppStore((state) => state.setIsRegeneratingSingle);
  const clearResults = useAppStore((state) => state.clearResults);

  const { generateComment, loading, error, clearError } = useApi();
  const { theme, toggleTheme } = useTheme();

  const handleGenerateComment = useCallback(async () => {
    if (isBatchMode) {
      if (selectedLocations.length === 0) return;
    } else {
      if (!selectedLocation) return;
    }

    clearError();
    clearResults();

    try {
      if (isBatchMode) {
        // Batch generation with improved parallel processing
        // Clear previous results before starting new batch
        setBatchResults([]);
        
        // Initialize results array with placeholders to maintain order
        const placeholderResults: BatchResult[] = selectedLocations.map((location: string) => ({
          location,
          success: false,
          loading: true,
          comment: null,
          metadata: null,
          error: null
        }));
        setBatchResults(placeholderResults);

        // Process all locations with controlled concurrency
        // This limits the number of simultaneous requests to prevent overwhelming the server
        // and provides incremental updates to the UI every CONCURRENT_LIMIT locations
        for (let i = 0; i < selectedLocations.length; i += BATCH_CONFIG.CONCURRENT_LIMIT) {
          const chunk = selectedLocations.slice(i, i + BATCH_CONFIG.CONCURRENT_LIMIT);
          const chunkIndices = chunk.map((_, idx) => i + idx);
          
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
              
              // Update state immediately with error
              setBatchResults(prev => {
                const newResults = [...prev];
                newResults[globalIdx] = errorResult;
                return newResults;
              });
              
              return errorResult;
            }
          });

          // Wait for all requests in the chunk to complete before processing next chunk
          // Results are updated immediately within each promise for progressive display
          await Promise.allSettled(chunkPromises);
        }
      } else {
        // Single location generation
        const result = await generateComment(selectedLocation!, {
          llmProvider,
        });
        setGeneratedComment(result);
      }
    } catch (err) {
      console.error('Failed to generate comment:', err);
    }
  }, [isBatchMode, selectedLocations, selectedLocation, clearError, clearResults, setBatchResults, generateComment, llmProvider, setGeneratedComment]);

  const handleCopyComment = useCallback((text: string) => {
    navigator.clipboard?.writeText(text);
    console.log('Copied:', text);
  }, []);


  const handleRegenerateSingle = useCallback(async () => {
    if (!selectedLocation) return;

    setIsRegeneratingSingle(true);
    clearError();

    try {
      const result = await generateComment(selectedLocation, {
        llmProvider,
        excludePrevious: true,
      });
      setGeneratedComment(result);
    } catch (err) {
      console.error('Failed to regenerate comment:', err);
    } finally {
      setIsRegeneratingSingle(false);
    }
  }, [selectedLocation, setIsRegeneratingSingle, clearError, generateComment, llmProvider, setGeneratedComment]);

  const handleRegenerateBatch = useCallback(async (locationName: string) => {
    setRegeneratingState(locationName, true);

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
      setRegeneratingState(locationName, false);
    }
  }, [setRegeneratingState, generateComment, llmProvider, setBatchResults]);

  const currentTime = useMemo(() => new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }), []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* ヘッダー */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Sun className="w-8 h-8 text-yellow-500 mr-3" />
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">天気コメント生成システム</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                React版 v1.0.0
              </span>
              <button
                onClick={toggleTheme}
                className="p-2 rounded-md border border-transparent hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                aria-label="Toggle theme"
              >
                {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* メインコンテンツ */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 左パネル: 設定 */}
            <div className="lg:col-span-1">
              <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center">
                    <Cloud className="w-5 h-5 mr-2 text-gray-600 dark:text-gray-400" />
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">設定</h2>
                  </div>
                </div>
                <div className="p-6">
                  <GenerateSettings
                    llmProvider={llmProvider}
                    onLlmProviderChange={setLlmProvider}
                    isBatchMode={isBatchMode}
                    onBatchModeChange={setIsBatchMode}
                  />
                </div>
              </div>

              <div className="mt-6 bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="p-6">
                  <LocationSelection
                    selectedLocation={selectedLocation}
                    selectedLocations={selectedLocations}
                    onLocationChange={setSelectedLocation}
                    onLocationsChange={setSelectedLocations}
                    isBatchMode={isBatchMode}
                  />
                </div>
              </div>

              {/* Batch mode warnings */}
              {isBatchMode && selectedLocations.length >= WARN_BATCH_LOCATIONS && (
                <div className="mt-6 bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
                  <div className="flex items-start">
                    <svg className="w-5 h-5 mr-2 mt-0.5 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L12.732 4c-.77-1.667-2.308-1.667-3.08 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div>
                      <div className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                        大量の地点が選択されています ({selectedLocations.length}地点)
                      </div>
                      <div className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
                        処理に時間がかかる可能性があります。
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* 生成時刻表示 */}
              <div className="mt-6 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
                <div className="flex items-center text-blue-700 dark:text-blue-300">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-sm font-medium">生成時刻: {currentTime}</span>
                </div>
              </div>

              {/* 生成ボタン */}
              <div className="mt-6">
                <button
                  type="button"
                  onClick={handleGenerateComment}
                  disabled={useMemo(() => 
                    ((isBatchMode && selectedLocations.length === 0) ||
                    (!isBatchMode && !selectedLocation)) ||
                    loading
                  , [isBatchMode, selectedLocations.length, selectedLocation, loading])}
                  className="w-full flex items-center justify-center space-x-2 bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>生成中...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      <span>{isBatchMode ? '一括コメント生成' : '🌦️ コメント生成'}</span>
                    </>
                  )}
                </button>
              </div>

              {/* エラー表示 */}
              {error && (
                <div className="mt-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg p-4">
                  <p className="text-red-800 dark:text-red-200 text-sm">{error}</p>
                </div>
              )}
            </div>

            {/* 右パネル: 結果表示 */}
            <div className="lg:col-span-2 space-y-6">
              {/* 一括生成結果 */}
              {isBatchMode && batchResults.length > 0 && (
                <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                  <div className="flex items-center mb-4">
                    <Sparkles className="w-5 h-5 mr-2 text-gray-600 dark:text-gray-400" />
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">一括生成結果</h2>
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    {useMemo(() => {
                      const successCount = batchResults.filter(r => r.success).length;
                      return `成功: ${successCount}件 / 全体: ${batchResults.length}件`;
                    }, [batchResults])}
                  </div>

                  <div className="space-y-4">
                    {batchResults.map((result, index) => (
                      <BatchResultItem
                        key={result.location}
                        result={result}
                        isExpanded={expandedLocations.has(result.location)}
                        onToggleExpanded={useCallback(() => handleToggleLocationExpanded(result.location), [handleToggleLocationExpanded, result.location])}
                        onRegenerate={useCallback(() => handleRegenerateBatch(result.location), [handleRegenerateBatch, result.location])}
                        isRegenerating={regeneratingStates[result.location] || false}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* 単一生成結果 */}
              {!isBatchMode && (
                <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                  <GeneratedCommentDisplay
                    comment={generatedComment}
                    onCopy={handleCopyComment}
                    onRegenerate={generatedComment ? handleRegenerateSingle : undefined}
                    isRegenerating={isRegeneratingSingle}
                  />
                </div>
              )}

              {/* 天気データ */}
              {!isBatchMode && generatedComment?.weather && (
                <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                  <WeatherDataDisplay
                    weather={generatedComment.weather}
                    metadata={generatedComment.metadata}
                  />
                </div>
              )}

              {/* 初期状態 */}
              {!loading && !generatedComment && batchResults.length === 0 && (
                <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                  <div className="text-center py-12">
                    <Sparkles className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <div className="text-lg font-medium text-gray-900 dark:text-white">コメント生成の準備完了</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                      左側のパネルから{isBatchMode ? '地点（複数選択可）' : '地点'}とプロバイダーを選択して、「{isBatchMode ? '一括' : ''}コメント生成」ボタンをクリックしてください
                    </div>

                    {/* Sample Comments */}
                    <div className="mt-8 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg text-left">
                      <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">サンプルコメント:</div>
                      <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                        <div><strong>晴れの日:</strong> 爽やかな朝ですね</div>
                        <div><strong>雨の日:</strong> 傘をお忘れなく</div>
                        <div><strong>曇りの日:</strong> 過ごしやすい一日です</div>
                        <div><strong>雪の日:</strong> 足元にお気をつけて</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

    </div>
  );
}

export default App
