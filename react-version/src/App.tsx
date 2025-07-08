import React, { useState } from 'react';
import { Cloud, Clock, Sparkles, MapPin } from 'lucide-react';
import type { Location, GeneratedComment, BatchResult } from '@mobile-comment-generator/shared';
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
import { useBatchGeneration } from './hooks/useBatchGeneration';
import { useUIState } from './hooks/useUIState';
import { REGIONS, getLocationInfo } from './constants/regions';
import { BATCH_CONFIG } from '../../src/config/constants';


// Constants for batch mode
const WARN_BATCH_LOCATIONS = 20;

function App() {
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [selectedLocations, setSelectedLocations] = useState<string[]>([]);
  const [llmProvider, setLlmProvider] = useState<'openai' | 'gemini' | 'anthropic'>('gemini');
  const [isBatchMode, setIsBatchMode] = useState(false);
  const [generatedComment, setGeneratedComment] = useState<GeneratedComment | null>(null);
  const [isRegeneratingSingle, setIsRegeneratingSingle] = useState(false);

  const { generateComment, loading, error, clearError } = useApi();
  const { theme, toggleTheme } = useTheme();
  const { batchResults, regeneratingStates, handleBatchGenerate, handleRegenerateBatch, setBatchResults } = useBatchGeneration({ generateComment, llmProvider });
  const { expandedLocations, toggleLocationExpanded, handleCopyComment, clearExpandedLocations } = useUIState();

  const handleGenerateComment = async () => {
    if (isBatchMode) {
      if (selectedLocations.length === 0) return;
    } else {
      if (!selectedLocation) return;
    }

    clearError();
    setGeneratedComment(null);
    setBatchResults([]);
    clearExpandedLocations();

    try {
      if (isBatchMode) {
        await handleBatchGenerate(selectedLocations);
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
  };


  const handleRegenerateSingle = async () => {
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
  };


  const currentTime = new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });

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
              {isBatchMode && selectedLocations.length >= WARN_BATCH_LOCATIONS && (
                <AlertBox
                  type="warning"
                  title="大量の地点が選択されています"
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
              />

              {/* Error display */}
              {error && (
                <AlertBox
                  type="error"
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
                    成功: {batchResults.filter(r => r.success).length}件 /
                    全体: {batchResults.length}件
                  </div>

                  <div className="space-y-4">
                    {batchResults.map((result, index) => (
                      <BatchResultItem
                        key={index}
                        result={result}
                        isExpanded={expandedLocations.has(result.location)}
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
