/**
 * Ad rendering
 */

import { MatchedProduct } from './request';

export type LayoutType = 'single' | 'vertical' | 'horizontal' | 'row';

/**
 * Render product ad in slot - Image fills the whole ad space
 */
export function renderProductAd(element: HTMLElement, product: MatchedProduct): void {
  // Clear existing content
  element.innerHTML = '';

  // Create ad container
  const adContainer = document.createElement('div');
  adContainer.className = 'aiads-container';
  adContainer.style.cssText = `
    width: 100%;
    height: 100%;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  `;

  // Create clickable link wrapper
  const adLink = document.createElement('div');
  adLink.style.cssText = `
    text-decoration: none;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: stretch;
    justify-content: center;
    cursor: pointer;
    overflow: hidden;
  `;

  // Handle click - open all landing URLs for multi-product, or single URL for single product
  adLink.addEventListener('click', (e) => {
    e.preventDefault();
    
    if (product.is_multi_product && product.products) {
      // Multi-product: open all landing URLs in separate tabs
      const landingUrls: string[] = [];
      
      // Collect all landing URLs from products array
      product.products.forEach((p: any) => {
        if (p.landing_url) {
          landingUrls.push(p.landing_url);
        }
      });
      
      // Also check for landing_url_2, landing_url_3, etc. (backward compatibility)
      if (product.landing_url) landingUrls.push(product.landing_url);
      let i = 2;
      while (product[`landing_url_${i}`]) {
        landingUrls.push(product[`landing_url_${i}`]);
        i++;
      }
      
      // Remove duplicates
      const uniqueUrls = Array.from(new Set(landingUrls));
      
      // Open all URLs in separate tabs
      uniqueUrls.forEach(url => {
        window.open(url, '_blank', 'noopener,noreferrer');
      });
      
      console.log(`Multi-product ad clicked: ${product.id} -> opened ${uniqueUrls.length} tabs:`, uniqueUrls);
    } else {
      // Single product: open single landing URL
      window.open(product.landing_url, '_blank', 'noopener,noreferrer');
      console.log(`Product ad clicked: ${product.id} -> ${product.landing_url}`);
    }
    // In production, send click event to backend
  });

  const imageWrapper = document.createElement('div');
  imageWrapper.style.cssText = `
    width: 100%;
    height: 100%;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  `;

  const img = document.createElement('img');
  img.src = product.edited_image_url || product.image_url;
  img.alt = product.name;
  img.style.cssText = `
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  `;
  img.onerror = () => {
    img.style.display = 'none';
    const fallbackText = document.createElement('div');
    fallbackText.textContent = product.name.substring(0, 30) + '...';
    fallbackText.style.cssText = `padding: 16px; text-align: center; color: #6c757d; font-size: 14px;`;
    imageWrapper.appendChild(fallbackText);
  };

  imageWrapper.appendChild(img);
  adLink.appendChild(imageWrapper);

  const adLabel = document.createElement('div');
  adLabel.textContent = 'Ad';
  adLabel.style.cssText = `
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(0, 0, 0, 0.6);
    color: white;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    z-index: 10;
  `;

  adContainer.appendChild(adLink);
  adContainer.appendChild(adLabel);
  element.appendChild(adContainer);

  // Track impression
  console.log(`Product ad rendered: ${product.id} (match: ${(product.match_score * 100).toFixed(1)}%)`);
  // In production, send impression event to backend
}

/**
 * Get layout type from element data attribute
 */
function getLayoutType(element: HTMLElement): LayoutType {
  const layout = element.getAttribute('data-aiads-layout')?.toLowerCase();
  if (layout === 'single' || layout === 'vertical' || layout === 'horizontal' || layout === 'row') {
    return layout;
  }
  // Default to horizontal/row for backward compatibility
  return 'horizontal';
}

/**
 * Render products based on layout type
 */
export function renderProducts(element: HTMLElement, products: MatchedProduct[], layout?: LayoutType): void {
  if (products.length === 0) {
    renderFallback(element);
    return;
  }

  const layoutType = layout || getLayoutType(element);

  // Single product layout
  if (layoutType === 'single') {
    renderSingleProduct(element, products[0]);
    return;
  }

  // Vertical layout
  if (layoutType === 'vertical') {
    renderVerticalProducts(element, products);
    return;
  }

  // Horizontal/row layout (default)
  renderHorizontalProducts(element, products);
}

/**
 * Render a single product
 */
function renderSingleProduct(element: HTMLElement, product: MatchedProduct): void {
  renderProductAd(element, product);
}

/**
 * Render multiple products in a row (up to 3 products)
 */
function renderHorizontalProducts(element: HTMLElement, products: MatchedProduct[]): void {
  if (products.length === 0) {
    renderFallback(element);
    return;
  }

  // Clear existing content
  element.innerHTML = '';

  // Create main ad container
  const adContainer = document.createElement('div');
  adContainer.className = 'aiads-container';
  adContainer.style.cssText = `
    width: 100%;
    height: 100%;
    position: relative;
    display: flex;
    flex-direction: row;
    align-items: stretch;
    gap: 4px;
    overflow: hidden;
  `;
  
  // Create all product items first, then set images to same height after they load
  products.forEach((product, index) => {
    const productItem = document.createElement('div');
    productItem.className = `aiads-product-item aiads-product-${index}`;
    productItem.style.cssText = `
      flex: 1;
      position: relative;
      display: flex;
      align-items: stretch;
      overflow: hidden;
      min-width: 0;
      height: 100%;
      background: transparent;
    `;

    const productLink = document.createElement('div');
    productLink.style.cssText = `
      text-decoration: none;
      width: 100%;
      height: 100%;
      display: flex;
      align-items: stretch;
      cursor: pointer;
      transition: opacity 0.2s;
      padding: 4px;
      box-sizing: border-box;
    `;

    // Add hover effect
    productLink.addEventListener('mouseenter', () => {
      productLink.style.opacity = '0.8';
    });
    productLink.addEventListener('mouseleave', () => {
      productLink.style.opacity = '1';
    });

    // Handle click - open all landing URLs for multi-product, or single URL for single product
    productLink.addEventListener('click', (e) => {
      e.preventDefault();
      
      if (product.is_multi_product && product.products) {
        // Multi-product: open all landing URLs in separate tabs
        const landingUrls: string[] = [];
        
        // Collect all landing URLs from products array
        product.products.forEach((p: any) => {
          if (p.landing_url) {
            landingUrls.push(p.landing_url);
          }
        });
        
        // Also check for landing_url_2, landing_url_3, etc. (backward compatibility)
        if (product.landing_url) landingUrls.push(product.landing_url);
        let i = 2;
        while (product[`landing_url_${i}`]) {
          landingUrls.push(product[`landing_url_${i}`]);
          i++;
        }
        
        // Remove duplicates
        const uniqueUrls = Array.from(new Set(landingUrls));
        
        // Open all URLs in separate tabs
        uniqueUrls.forEach(url => {
          window.open(url, '_blank', 'noopener,noreferrer');
        });
        
        console.log(`Multi-product ad clicked: ${product.id} -> opened ${uniqueUrls.length} tabs:`, uniqueUrls);
      } else {
        // Single product: open single landing URL
        window.open(product.landing_url, '_blank', 'noopener,noreferrer');
        console.log(`Product ${index + 1} clicked: ${product.id} -> ${product.landing_url}`);
      }
      // In production, send click event to backend
    });

    const imageWrapper = document.createElement('div');
    imageWrapper.style.cssText = `
      flex: 1;
      min-width: 0;
      min-height: 0;
      overflow: hidden;
    `;

    const img = document.createElement('img');
    img.src = product.edited_image_url || product.image_url;
    img.alt = product.name;
    img.style.cssText = `
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    `;
    imageWrapper.appendChild(img);

    img.onerror = () => {
      img.style.display = 'none';
      const fallbackText = document.createElement('div');
      fallbackText.textContent = product.name.substring(0, 20) + '...';
      fallbackText.style.cssText = `
        padding: 8px;
        text-align: center;
        color: #6c757d;
        font-size: 11px;
        word-break: break-word;
      `;
      imageWrapper.appendChild(fallbackText);
    };

    productLink.appendChild(imageWrapper);
    productItem.appendChild(productLink);
    adContainer.appendChild(productItem);
  });

  // Add "Ad" label
  const adLabel = document.createElement('div');
  adLabel.textContent = 'Ad';
  adLabel.style.cssText = `
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(0, 0, 0, 0.6);
    color: white;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    z-index: 10;
  `;

  adContainer.appendChild(adLabel);
  element.appendChild(adContainer);

  // Track impression
  console.log(`Rendered ${products.length} product ad(s) in row layout`);
  // In production, send impression event to backend
}

/**
 * Render multiple products vertically (stacked)
 */
function renderVerticalProducts(element: HTMLElement, products: MatchedProduct[]): void {
  if (products.length === 0) {
    renderFallback(element);
    return;
  }

  // Clear existing content
  element.innerHTML = '';

  // Create main ad container
  const adContainer = document.createElement('div');
  adContainer.className = 'aiads-container';
  adContainer.style.cssText = `
    width: 100%;
    height: 100%;
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 4px;
    overflow: hidden;
  `;
  
  // Limit to 3 products for vertical layout
  const productsToShow = products.slice(0, 3);
  
  productsToShow.forEach((product, index) => {
    const productItem = document.createElement('div');
    productItem.className = `aiads-product-item aiads-product-${index}`;
    productItem.style.cssText = `
      flex: 1;
      position: relative;
      display: flex;
      align-items: stretch;
      overflow: hidden;
      min-height: 0;
      width: 100%;
      background: transparent;
    `;

    const productLink = document.createElement('div');
    productLink.style.cssText = `
      text-decoration: none;
      width: 100%;
      height: 100%;
      display: flex;
      align-items: stretch;
      cursor: pointer;
      transition: opacity 0.2s;
      padding: 4px;
      box-sizing: border-box;
    `;

    // Add hover effect
    productLink.addEventListener('mouseenter', () => {
      productLink.style.opacity = '0.8';
    });
    productLink.addEventListener('mouseleave', () => {
      productLink.style.opacity = '1';
    });

    // Handle click - open all landing URLs for multi-product, or single URL for single product
    productLink.addEventListener('click', (e) => {
      e.preventDefault();
      
      if (product.is_multi_product && product.products) {
        // Multi-product: open all landing URLs in separate tabs
        const landingUrls: string[] = [];
        
        // Collect all landing URLs from products array
        product.products.forEach((p: any) => {
          if (p.landing_url) {
            landingUrls.push(p.landing_url);
          }
        });
        
        // Also check for landing_url_2, landing_url_3, etc. (backward compatibility)
        if (product.landing_url) landingUrls.push(product.landing_url);
        let i = 2;
        while (product[`landing_url_${i}`]) {
          landingUrls.push(product[`landing_url_${i}`]);
          i++;
        }
        
        // Remove duplicates
        const uniqueUrls = Array.from(new Set(landingUrls));
        
        // Open all URLs in separate tabs
        uniqueUrls.forEach(url => {
          window.open(url, '_blank', 'noopener,noreferrer');
        });
        
        console.log(`Multi-product ad clicked: ${product.id} -> opened ${uniqueUrls.length} tabs:`, uniqueUrls);
      } else {
        // Single product: open single landing URL
        window.open(product.landing_url, '_blank', 'noopener,noreferrer');
        console.log(`Product ${index + 1} clicked: ${product.id} -> ${product.landing_url}`);
      }
    });

    const imageWrapper = document.createElement('div');
    imageWrapper.style.cssText = `
      flex: 1;
      min-height: 0;
      overflow: hidden;
    `;

    const img = document.createElement('img');
    img.src = product.edited_image_url || product.image_url;
    img.alt = product.name;
    img.style.cssText = `
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    `;
    imageWrapper.appendChild(img);

    img.onerror = () => {
      img.style.display = 'none';
      const fallbackText = document.createElement('div');
      fallbackText.textContent = product.name.substring(0, 20) + '...';
      fallbackText.style.cssText = `
        padding: 8px;
        text-align: center;
        color: #6c757d;
        font-size: 11px;
        word-break: break-word;
      `;
      imageWrapper.appendChild(fallbackText);
    };

    productLink.appendChild(imageWrapper);
    productItem.appendChild(productLink);
    adContainer.appendChild(productItem);
  });

  // Add "Ad" label
  const adLabel = document.createElement('div');
  adLabel.textContent = 'Ad';
  adLabel.style.cssText = `
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(0, 0, 0, 0.6);
    color: white;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    z-index: 10;
  `;

  adContainer.appendChild(adLabel);
  element.appendChild(adContainer);

  // Track impression
  console.log(`Rendered ${productsToShow.length} product ad(s) in vertical layout`);
}

/**
 * Render fallback message when no ad is available
 */
export function renderFallback(element: HTMLElement): void {
  element.innerHTML = '';

  const fallbackDiv = document.createElement('div');
  fallbackDiv.className = 'aiads-fallback';
  fallbackDiv.style.cssText = `
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    color: #6c757d;
    font-size: 14px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  `;
  fallbackDiv.textContent = 'Advertisement';

  element.appendChild(fallbackDiv);
}

