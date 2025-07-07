import React, { useState, useEffect, useMemo } from 'react';
import { Search, MapPin, Loader2, CheckCircle, XCircle } from 'lucide-react';
import type { Location } from '@mobile-comment-generator/shared';
import { createWeatherCommentComposable } from '@mobile-comment-generator/shared/composables';
import { 
  createLocationSelectionLogic, 
  REGIONS,
  getAreaName,
  getLocationsByRegion 
} from '@mobile-comment-generator/shared/composables';

interface LocationSelectionProps {
  selectedLocation: Location | null;
  selectedLocations: string[];
  onLocationChange: (location: Location) => void;
  onLocationsChange: (locations: string[]) => void;
  isBatchMode: boolean;
  className?: string;
}

export const LocationSelection: React.FC<LocationSelectionProps> = ({
  selectedLocation,
  selectedLocations: externalSelectedLocations,
  onLocationChange,
  onLocationsChange,
  isBatchMode,
  className = '',
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  
  const { getLocations } = createWeatherCommentComposable();
  
  // 共通ロジックを使用
  const locationLogic = useMemo(() => {
    const logic = createLocationSelectionLogic({
      selectedLocations: externalSelectedLocations
    });
    
    // APIクライアントを設定
    (logic as any).setApiClient({
      fetchLocations: async () => {
        try {
          const data = await getLocations();
          return {
            success: true,
            data: data.map(loc => ({
              ...loc,
              region: loc.region || getAreaName(loc.name),
            }))
          };
        } catch (error) {
          return { success: false };
        }
      }
    });
    
    return logic;
  }, []);

  // State from logic
  const [state, setState] = useState({
    locations: locationLogic.locations,
    isLoading: locationLogic.isLoading,
    error: locationLogic.error,
  });

  useEffect(() => {
    let isMounted = true;
    
    const loadData = async () => {
      await locationLogic.loadLocations();
      
      if (isMounted) {
        setState({
          locations: locationLogic.locations,
          isLoading: locationLogic.isLoading,
          error: locationLogic.error,
        });
        
        // 初回読み込み時に外部の選択状態を反映
        if (externalSelectedLocations.length > 0) {
          locationLogic.selectedLocations = [...externalSelectedLocations];
        }
      }
    };

    loadData();
    
    return () => {
      isMounted = false;
    };
  }, []);

  // 外部の選択状態が変更されたときに同期
  useEffect(() => {
    locationLogic.selectedLocations = [...externalSelectedLocations];
  }, [externalSelectedLocations]);

  const filteredLocations = useMemo(() => {
    return state.locations.filter(location =>
      location.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      location.prefecture.toLowerCase().includes(searchTerm.toLowerCase()) ||
      location.region.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [state.locations, searchTerm]);

  const selectAllLocations = () => {
    const allLocationNames = state.locations.map(loc => loc.name);
    onLocationsChange(allLocationNames);
  };

  const clearAllLocations = () => {
    onLocationsChange([]);
  };

  const selectRegionLocations = (regionName: string) => {
    const regionLocationNames = getLocationsByRegion(regionName);
    const allSelected = regionLocationNames.every(name => 
      externalSelectedLocations.includes(name)
    );
    
    if (allSelected) {
      // Remove all locations from this region
      const updatedLocations = externalSelectedLocations.filter(name => 
        !regionLocationNames.includes(name)
      );
      onLocationsChange(updatedLocations);
    } else {
      // Add missing locations from this region
      const newLocations = regionLocationNames.filter(name => 
        !externalSelectedLocations.includes(name)
      );
      const updatedLocations = [...externalSelectedLocations, ...newLocations];
      onLocationsChange(updatedLocations);
    }
  };

  const isRegionSelected = (regionName: string) => {
    const regionLocationNames = getLocationsByRegion(regionName);
    return regionLocationNames.length > 0 && 
      regionLocationNames.every(name => externalSelectedLocations.includes(name));
  };

  const toggleLocationSelection = (locationName: string) => {
    if (externalSelectedLocations.includes(locationName)) {
      onLocationsChange(externalSelectedLocations.filter(name => name !== locationName));
    } else {
      onLocationsChange([...externalSelectedLocations, locationName]);
    }
  };

  if (state.isLoading) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          <span className="ml-2 text-gray-600 dark:text-gray-300">読み込み中...</span>
        </div>
      </div>
    );
  }

  if (state.error) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg p-4">
          <p className="text-red-800">{state.error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div>
        <label htmlFor="location-search" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {isBatchMode ? '地点選択（複数選択可）' : '地点選択'}
        </label>
        
        {/* Batch mode controls */}
        {isBatchMode && (
          <div className="space-y-3 mb-4">
            {/* Quick select buttons */}
            <div className="space-y-2">
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={selectAllLocations}
                  className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-md border border-green-200 bg-green-50 text-green-700 hover:bg-green-100 transition-colors"
                  aria-label="すべての地点を選択"
                >
                  <CheckCircle className="w-3 h-3 mr-1" />
                  🌍 全地点選択
                </button>
                <button
                  onClick={clearAllLocations}
                  className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-md border border-red-200 bg-red-50 text-red-700 hover:bg-red-100 transition-colors"
                  aria-label="選択をクリア"
                >
                  <XCircle className="w-3 h-3 mr-1" />
                  クリア
                </button>
              </div>
              
              <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">地域選択:</div>
              <div className="flex flex-wrap gap-1">
                {REGIONS.map((region) => (
                  <button
                    key={region}
                    onClick={() => selectRegionLocations(region)}
                    className={`px-2 py-1 text-xs font-medium rounded-md transition-colors ${
                      isRegionSelected(region)
                        ? 'bg-blue-500 text-white border border-blue-500'
                        : 'bg-gray-50 text-gray-700 border border-gray-200 hover:bg-gray-100'
                    }`}
                    aria-label={`${region}の地点を${isRegionSelected(region) ? '選択解除' : '選択'}`}
                  >
                    {region}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Selected count */}
            <div className="text-sm text-gray-600 dark:text-gray-400">
              選択中: {externalSelectedLocations.length}地点
            </div>
          </div>
        )}

        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            id="location-search"
            type="text"
            placeholder="地点名または地域名で検索..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 transition-colors"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Single mode selected location display */}
      {!isBatchMode && selectedLocation && (
        <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <MapPin className="w-4 h-4 text-blue-600" />
            <div>
              <div className="font-medium text-blue-900 dark:text-blue-300">{selectedLocation.name}</div>
              <div className="text-sm text-blue-700 dark:text-blue-400">{selectedLocation.prefecture} - {selectedLocation.region}</div>
            </div>
          </div>
        </div>
      )}
      
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg max-h-64 overflow-y-auto">
        {filteredLocations.length === 0 ? (
          <div className="p-4 text-center text-gray-500 dark:text-gray-400">
            検索条件に一致する地点が見つかりません
          </div>
        ) : (
          filteredLocations.map((location) => (
            <button
              key={location.id}
              className={`w-full text-left p-3 hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-100 dark:border-gray-700 last:border-b-0 flex items-center space-x-2 transition-colors ${
                isBatchMode
                  ? externalSelectedLocations.includes(location.name)
                    ? 'bg-blue-50 dark:bg-blue-900/30'
                    : ''
                  : selectedLocation?.id === location.id
                    ? 'bg-blue-50 dark:bg-blue-900/30'
                    : ''
              }`}
              onClick={() => {
                if (isBatchMode) {
                  toggleLocationSelection(location.name);
                } else {
                  onLocationChange(location);
                }
              }}
              aria-label={`${location.name}を${isBatchMode && externalSelectedLocations.includes(location.name) ? '選択解除' : '選択'}`}
            >
              <MapPin className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="font-medium text-gray-900 dark:text-gray-100 truncate">{location.name}</div>
                <div className="text-sm text-gray-500 dark:text-gray-400 truncate">{location.prefecture} - {location.region}</div>
              </div>
              {isBatchMode && externalSelectedLocations.includes(location.name) && (
                <CheckCircle className="w-4 h-4 text-blue-500 flex-shrink-0" />
              )}
            </button>
          ))
        )}
      </div>
    </div>
  );
};