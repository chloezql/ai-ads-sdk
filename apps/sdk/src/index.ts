/**
 * AI Ads SDK - Main entry point
 * Context-aware ad serving without user tracking
 */

import { AiAdsSDK, AiAdsConfig } from './init';

// Global SDK instance
let sdkInstance: AiAdsSDK | null = null;

/**
 * Initialize the AI Ads SDK
 */
export function init(config: AiAdsConfig): AiAdsSDK {
  if (sdkInstance) {
    console.warn('[AiAds] SDK already initialized');
    return sdkInstance;
  }

  sdkInstance = new AiAdsSDK(config);

  // Auto-load ads if enabled
  if (config.autoLoad !== false) {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        sdkInstance?.loadAllAds();
      });
    } else {
      // DOM already loaded
      sdkInstance.loadAllAds();
    }
  }

  return sdkInstance;
}

/**
 * Get the current SDK instance
 */
export function getInstance(): AiAdsSDK | null {
  return sdkInstance;
}

// Expose to window for script tag usage
declare global {
  interface Window {
    aiAds: {
      init: typeof init;
      getInstance: typeof getInstance;
    };
  }
}

if (typeof window !== 'undefined') {
  window.aiAds = {
    init,
    getInstance,
  };
}

// Export for module usage
export { AiAdsSDK, AiAdsConfig };
export { clearCacheForUrl, clearAllCache, getCacheStats } from './cache';
export default { init, getInstance };

