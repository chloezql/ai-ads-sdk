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
        // Get layout type from element data attribute
        const layout = element.getAttribute('data-aiads-layout')?.toLowerCase();
        renderProducts(element, response.matched_products, layout as any);
        this.log(`Rendered ${response.matched_products.length} matched product(s) with layout: ${layout || 'horizontal'}`);
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
   * Makes one API request and distributes products across slots
   */
  async loadAllAds(): Promise<void> {
    this.log('Loading all ads');

    // Find all ad slots
    const slots = Array.from(document.querySelectorAll<HTMLElement>('[data-aiads-slot]'));
    this.log(`Found ${slots.length} ad slots`);

    if (slots.length === 0) {
      return;
    }

    // Extract context once for all slots
    this.extractContext();
    if (!this.pageContext || !this.envContext) {
      console.error('Failed to extract context');
      slots.forEach(slot => {
        const element = slot.id ? document.getElementById(slot.id) : slot;
        if (element) renderFallback(element);
      });
      return;
    }

    // Use the first slot's dimensions for the API request (or average)
    // In practice, we'll use the first slot or make a generic request
    const firstSlot = slots[0];
    const slotDimensions = getAdSlotDimensions(firstSlot);
    
    // Make one API request for all slots
    let response: Awaited<ReturnType<typeof requestContext>>;
    try {
      const slotId = firstSlot.id || firstSlot.getAttribute('data-aiads-slot') || 'all-slots';
      response = await requestContext(
        this.config.apiEndpoint,
        this.config.publisherId,
        this.pageContext,
        this.envContext,
        slotId,
        slotDimensions
      );
      this.log('Context response:', response);
    } catch (error) {
      console.error('Error requesting context:', error);
      slots.forEach(slot => {
        const element = slot.id ? document.getElementById(slot.id) : slot;
        if (element) renderFallback(element);
      });
      return;
    }

    // Get all products
    const allProducts = response.success && response.matched_products ? response.matched_products : [];
    
    if (allProducts.length === 0) {
      this.log('No products available, rendering fallback for all slots');
      slots.forEach(slot => {
        const element = slot.id ? document.getElementById(slot.id) : slot;
        if (element) renderFallback(element);
      });
      return;
    }

    // Separate slots by layout type
    const singleSlots: Array<{ element: HTMLElement; slot: HTMLElement }> = [];
    const verticalSlots: Array<{ element: HTMLElement; slot: HTMLElement }> = [];
    const horizontalSlots: Array<{ element: HTMLElement; slot: HTMLElement }> = [];
    
    for (const slot of slots) {
      const element = slot.id ? document.getElementById(slot.id) : slot;
      if (!element) {
        console.warn('Ad slot element not found:', slot);
        continue;
      }
      
      const layout = element.getAttribute('data-aiads-layout')?.toLowerCase() || 'horizontal';
      
      if (layout === 'single') {
        singleSlots.push({ element, slot });
      } else if (layout === 'vertical') {
        verticalSlots.push({ element, slot });
      } else {
        horizontalSlots.push({ element, slot });
      }
    }
    
    // Distribute products across slots
    let productIndex = 0;
    
    // 1. First, assign products to single slots (one per slot)
    for (const { element } of singleSlots) {
      if (productIndex < allProducts.length) {
        const product = allProducts[productIndex];
        renderProducts(element, [product], 'single');
        this.log(`Rendered product ${productIndex + 1} in slot ${element.id || 'unknown'} (single layout)`);
        productIndex++;
      } else {
        renderFallback(element);
      }
    }
    
    // 2. Then, distribute remaining products across vertical slots
    if (verticalSlots.length > 0) {
      const remainingProducts = allProducts.slice(productIndex);
      const totalRemaining = remainingProducts.length;
      const productsPerSlot = Math.floor(totalRemaining / verticalSlots.length);
      const extraProducts = totalRemaining % verticalSlots.length;
      
      let currentIndex = 0;
      for (let i = 0; i < verticalSlots.length; i++) {
        const { element } = verticalSlots[i];
        // First slots get one extra product if there are leftovers
        const productsForThisSlot = productsPerSlot + (i < extraProducts ? 1 : 0);
        const slotProducts = remainingProducts.slice(currentIndex, currentIndex + productsForThisSlot);
        
        if (slotProducts.length > 0) {
          renderProducts(element, slotProducts, 'vertical');
          this.log(`Rendered ${slotProducts.length} product(s) in slot ${element.id || 'unknown'} (vertical layout)`);
          currentIndex += productsForThisSlot;
        } else {
          renderFallback(element);
        }
      }
      productIndex += totalRemaining;
    }
    
    // 3. Finally, assign remaining products to horizontal slots (only first one to avoid duplication)
    if (horizontalSlots.length > 0) {
      const remainingProducts = allProducts.slice(productIndex);
      if (remainingProducts.length > 0 && horizontalSlots.length > 0) {
        // Only assign to first horizontal slot to avoid duplication
        renderProducts(horizontalSlots[0].element, remainingProducts, 'horizontal');
        this.log(`Rendered ${remainingProducts.length} product(s) in slot ${horizontalSlots[0].element.id || 'unknown'} (horizontal layout)`);
        productIndex += remainingProducts.length;
        
        // Show fallback for other horizontal slots
        for (let i = 1; i < horizontalSlots.length; i++) {
          renderFallback(horizontalSlots[i].element);
        }
      } else {
        horizontalSlots.forEach(({ element }) => renderFallback(element));
      }
    }

    this.log('All ads loaded and distributed');
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

