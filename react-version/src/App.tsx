import React, { useCallback, useMemo } from 'react';
import { Cloud, Clock, Sparkles, MapPin } from 'lucide-react';
import type { Location, BatchResult } from '@mobile-comment-generator/shared';
import { BATCH_CONFIG } from '@mobile-comment-generator/shared';

import { LocationSelection } from './components/LocationSelection';
import { GenerateSettings } from './components/GenerateSettings';
import { GeneratedCommentDisplay } from './components/GeneratedComment';
import { WeatherDataDisplay } from './components/WeatherData';
import { BatchResultItem } from './components/BatchResultItem';
import { Header } from './components/Header';
import { EmptyState } from './components/EmptyState';
import { GenerateButton } from './components/GenerateButton';
import { Card } from './components/Card';
import { AlertBox } from './components/AlertBox';
import { useApi } from './hooks/useApi';
import { useTheme } from './hooks/useTheme';
import { useAppStore } from './stores/useAppStore';
import { getLocationInfo } from './constants/regions';

type BatchResultWithId = BatchResult & { id: string };

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
  const setRegeneratingState = useAppStore((state) => state.setRegeneratingState);
  const setIsRegeneratingSingle = useAppStore((state) => state.setIsRegeneratingSingle);
  const clearResults = useAppStore((state) => state.clearResults);
  const setGeneratedAt = useAppStore((state) => state.setGeneratedAt);

  // Hooks
  const { generateComment, loading, error, clearError } = useApi();
  const { theme, toggleTheme } = useTheme();

  // Handle single generation
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
        // Batch generation
        // Initialize all locations with pending state
        const initialResults: BatchResult[] = selectedLocations.map((locationName, index) => ({
          success: false,
          location: locationName,
          error: '生成中...',
          id: `${locationName}-${Date.now()}-${index}`
        } as BatchResult & { id: string }));
        setBatchResults(initialResults);

        // Process each location
        for (let i = 0; i < selectedLocations.length; i++) {
          const locationName = selectedLocations[i];
          try {
            const locationInfo = getLocationInfo(locationName);
            const locationObj: Location = {
              id: locationName,
              name: locationName,
              prefecture: locationInfo.prefecture,
              region: locationInfo.region
            };

            const result = await generateComment(locationObj, { llmProvider });
            
            // Update the specific result
            setBatchResults((prevResults) => {
              const newResults = [...prevResults];
              newResults[i] = {
                success: true,
                location: locationName,
                comment: result.comment,
                metadata: result.metadata,
                weather: result.weather,
                adviceComment: result.adviceComment,
                id: newResults[i].id // Keep the same ID
              } as BatchResult & { id: string };
              return newResults;
            });
          } catch (error) {
            // Update with error
            setBatchResults((prevResults) => {
              const newResults = [...prevResults];
              newResults[i] = {
                success: false,
                location: locationName,
                error: error instanceof Error ? error.message : 'コメント生成に失敗しました',
                id: newResults[i].id // Keep the same ID
              } as BatchResult & { id: string };
              return newResults;
            });
          }
        }
        setGeneratedAt(new Date().toISOString());
      } else {
        // Single location generation
        const result = await generateComment(selectedLocation as Location, {
          llmProvider,
        });
        setGeneratedComment(result);
        setGeneratedAt(new Date().toISOString());
      }
    } catch (err) {
      console.error('Failed to generate comment:', err);
    }
  }, [isBatchMode, selectedLocations, selectedLocation, generateComment, llmProvider, clearError, clearResults, setBatchResults, setGeneratedComment, setGeneratedAt]);

  // Handle copy comment
  const handleCopyComment = useCallback((text: string) => {
    navigator.clipboard?.writeText(text);
    console.log('Copied:', text);
  }, []);

  // Handle regenerate single
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
  }, [selectedLocation, generateComment, llmProvider, clearError, setGeneratedComment, setIsRegeneratingSingle]);

  // Handle regenerate batch
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
  }, [generateComment, llmProvider, setBatchResults, setRegeneratingState]);

  const currentTime = new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });

  const batchResultsStats = useMemo(() => {
    const successCount = batchResults.filter(r => r.success).length;
    return `成功: ${successCount}件 / 全体: ${batchResults.length}件`;
  }, [batchResults]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header component */}
      <Header 
        version="v1.0.0"
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      {/* メインコンテンツ */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 左パネル: 設定 */}
            <div className="lg:col-span-1">
              {/* Settings Card */}
              <Card
                title="設定"
                icon={Cloud}
              >
                <GenerateSettings
                  llmProvider={llmProvider}
                  onLlmProviderChange={setLlmProvider}
                  isBatchMode={isBatchMode}
                  onBatchModeChange={setIsBatchMode}
                />
              </Card>

              {/* Location Selection Card */}
              <Card title="地点選択" icon={MapPin} className="mt-6">
                <LocationSelection
                  selectedLocation={selectedLocation}
                  selectedLocations={selectedLocations}
                  onLocationChange={setSelectedLocation}
                  onLocationsChange={setSelectedLocations}
                  isBatchMode={isBatchMode}
                />
              </Card>

              {/* Batch mode warning */}
              {isBatchMode && selectedLocations.length >= BATCH_CONFIG.WARN_BATCH_LOCATIONS && (
                <AlertBox
                  type="warning"
                  title="大量の地点が選択されています"
                  className="mt-6"
                >
                  <div>
                    <div className="text-sm font-medium">
                      大量の地点が選択されています ({selectedLocations.length}地点)
                    </div>
                    <div className="text-xs mt-1">
                      処理に時間がかかる可能性があります。
                    </div>
                  </div>
                </AlertBox>
              )}

              {/* 生成時刻表示 */}
              <AlertBox
                type="info"
                className="mt-6"
              >
                <div className="flex items-center">
                  <Clock className="w-4 h-4 mr-2" />
                  <span className="text-sm font-medium">生成時刻: {currentTime}</span>
                </div>
              </AlertBox>

              {/* Generate Button */}
              <GenerateButton
                onClick={handleGenerateComment}
                disabled={
                  ((isBatchMode && selectedLocations.length === 0) ||
                  (!isBatchMode && !selectedLocation)) ||
                  loading
                }
                loading={loading}
                isBatchMode={isBatchMode}
                selectedCount={isBatchMode ? selectedLocations.length : 0}
                className="mt-6"
              />

              {/* Error display */}
              {error && (
                <AlertBox
                  type="error"
                  className="mt-6"
                >
                  <p className="text-sm">{error}</p>
                </AlertBox>
              )}
            </div>

            {/* 右パネル: 結果表示 */}
            <div className="lg:col-span-2 space-y-6">
              {/* 一括生成結果 */}
              {isBatchMode && batchResults.length > 0 && (
                <Card title="一括生成結果" icon={Cloud}>
                  <div className="flex items-center mb-4">
                    <Sparkles className="w-5 h-5 mr-2 text-gray-600 dark:text-gray-400" />
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">一括生成結果</h2>
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    {batchResultsStats}
                  </div>

                  <div className="space-y-4">
                    {batchResults.map((result, index) => (
                      <BatchResultItem
                        key={(result as BatchResultWithId).id || `${result.location}-${index}`}
                        result={result}
                        isExpanded={expandedLocations[result.location] || false}
                        onToggleExpanded={() => toggleLocationExpanded(result.location)}
                        onRegenerate={() => handleRegenerateBatch(result.location)}
                        isRegenerating={regeneratingStates[result.location] || false}
                      />
                    ))}
                  </div>
                </Card>
              )}

              {/* 単一生成結果 */}
              {!isBatchMode && (
                <Card title="生成結果" icon={Cloud}>
                  <GeneratedCommentDisplay
                    comment={generatedComment}
                    onCopy={handleCopyComment}
                    onRegenerate={generatedComment ? handleRegenerateSingle : undefined}
                    isRegenerating={isRegeneratingSingle}
                  />
                </Card>
              )}

              {/* 天気データ */}
              {!isBatchMode && generatedComment?.weather && (
                <Card title="天気情報" icon={Cloud}>
                  <WeatherDataDisplay
                    weather={generatedComment.weather}
                    metadata={generatedComment.metadata}
                  />
                </Card>
              )}

              {/* Empty State */}
              {!loading && !generatedComment && batchResults.length === 0 && (
                <div>
                  <EmptyState 
                    isBatchMode={isBatchMode}
                  />
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