/**
 * SDK initialization
 */

import { extractPageContext, extractEnvironmentContext, getAdSlotDimensions } from './context';
import { requestContext } from './request';
import { renderProductAd, renderProducts, renderFallback } from './render';
import { clearCacheForUrl, clearAllCache, getCacheStats } from './cache';

export interface AiAdsConfig {
  apiEndpoint: string;
  publisherId: string;
  autoLoad?: boolean;
  debug?: boolean;
}

export class AiAdsSDK {
  private config: AiAdsConfig;
  private pageContext: ReturnType<typeof extractPageContext> | null = null;
  private envContext: ReturnType<typeof extractEnvironmentContext> | null = null;

  constructor(config: AiAdsConfig) {
    this.config = {
      autoLoad: true,
      debug: false,
      ...config,
    };

    if (!this.config.apiEndpoint) {
      throw new Error('apiEndpoint is required');
    }

    if (!this.config.publisherId) {
      throw new Error('publisherId is required');
    }

    this.log('SDK initialized', this.config);
  }

  private log(...args: any[]): void {
    if (this.config.debug) {
      console.log('[AiAds]', ...args);
    }
  }

  /**
   * Extract page context once
   */
  private extractContext(): void {
    if (!this.pageContext) {
      this.pageContext = extractPageContext();
      this.log('Page context extracted:', this.pageContext);
    }

    if (!this.envContext) {
      this.envContext = extractEnvironmentContext();
      this.log('Environment context extracted:', this.envContext);
    }
  }

  /**
   * Load ad into a specific slot
   */
  async loadAd(slotId: string): Promise<void> {
    this.log(`Loading ad for slot: ${slotId}`);

    // Find ad slot element
    const element = document.getElementById(slotId);
    if (!element) {
      console.error(`Ad slot not found: ${slotId}`);
      return;
    }

    try {
      // Extract context
      this.extractContext();

      if (!this.pageContext || !this.envContext) {
        throw new Error('Failed to extract context');
      }

      // Get slot dimensions
      const slotDimensions = getAdSlotDimensions(element);
      this.log(`Slot dimensions:`, slotDimensions);

      // Request context and matched products
      const response = await requestContext(
        this.config.apiEndpoint,
        this.config.publisherId,
        this.pageContext,
        this.envContext,
        slotId,
        slotDimensions
      );

      this.log('Context response:', response);

      // Render products or fallback
      if (response.success && response.matched_products && response.matched_products.length > 0) {
        renderProducts(element, response.matched_products);
        this.log(`Rendered ${response.matched_products.length} matched product(s)`);
      } else {
        renderFallback(element);
        this.log('No products available, rendered fallback');
      }
    } catch (error) {
      console.error(`Error loading ad for slot ${slotId}:`, error);
      renderFallback(element);
    }
  }

  /**
   * Load all ads on the page
   */
  async loadAllAds(): Promise<void> {
    this.log('Loading all ads');

    // Find all ad slots
    const slots = document.querySelectorAll<HTMLElement>('[data-aiads-slot]');
    this.log(`Found ${slots.length} ad slots`);

    // Load each slot
    const promises = Array.from(slots).map((slot) => {
      const slotId = slot.id || slot.getAttribute('data-aiads-slot') || '';
      if (!slotId) {
        console.warn('Ad slot missing ID:', slot);
        return Promise.resolve();
      }
      return this.loadAd(slotId);
    });

    await Promise.all(promises);
    this.log('All ads loaded');
  }

  /**
   * Refresh a specific ad slot
   */
  async refreshAd(slotId: string): Promise<void> {
    this.log(`Refreshing ad for slot: ${slotId}`);
    
    // Clear cache for current URL before refreshing
    if (this.pageContext) {
      clearCacheForUrl(this.pageContext.url);
    }
    
    // Re-extract context (in case page changed)
    this.pageContext = null;
    this.envContext = null;
    
    await this.loadAd(slotId);
  }

  /**
   * Clear cache for a specific URL
   */
  clearCache(url: string): void {
    clearCacheForUrl(url);
    this.log(`Cache cleared for URL: ${url}`);
  }

  /**
   * Clear all cached ads
   */
  clearAllCache(): void {
    clearAllCache();
    this.log('All cache cleared');
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): { count: number; urls: string[] } {
    return getCacheStats();
  }
}

