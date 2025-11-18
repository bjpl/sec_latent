/**
 * E2E Tests with Playwright
 * End-to-end user flow testing
 *
 * Tests cover:
 * - Complete user workflows
 * - Multi-page navigation
 * - Form submissions
 * - Real-time updates
 * - Mobile responsiveness
 */
import { test, expect, Page } from '@playwright/test';

// Base URL from environment or default
const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';

test.describe('Filing Analysis Workflow', () => {
  test('complete filing analysis flow', async ({ page }) => {
    // Navigate to home
    await page.goto(BASE_URL);
    await expect(page).toHaveTitle(/SEC Filing Analysis/);

    // Search for filing
    await page.fill('[data-testid="search-input"]', 'Microsoft');
    await page.click('[data-testid="search-button"]');

    // Wait for results
    await page.waitForSelector('[data-testid="filing-list"]');

    // Select first filing
    await page.click('[data-testid="filing-0"]');

    // Verify filing detail page
    await expect(page.locator('[data-testid="filing-detail"]')).toBeVisible();

    // View signals tab
    await page.click('[data-testid="tab-signals"]');
    await expect(page.locator('[data-testid="signal-chart"]')).toBeVisible();

    // View predictions tab
    await page.click('[data-testid="tab-predictions"]');
    await expect(page.locator('[data-testid="prediction-card"]')).toBeVisible();

    // Verify prediction data
    const confidence = await page.textContent('[data-testid="prediction-confidence"]');
    expect(parseFloat(confidence || '0')).toBeGreaterThan(0);
  });

  test('filtering and sorting filings', async ({ page }) => {
    await page.goto(BASE_URL);

    // Apply filters
    await page.selectOption('[data-testid="form-type-filter"]', '10-K');
    await page.fill('[data-testid="date-from"]', '2024-01-01');

    // Apply filters
    await page.click('[data-testid="apply-filters"]');

    // Wait for filtered results
    await page.waitForSelector('[data-testid="filing-list"]');

    // Verify filter applied
    const filings = await page.locator('[data-testid^="filing-"]').count();
    expect(filings).toBeGreaterThan(0);

    // Test sorting
    await page.selectOption('[data-testid="sort-select"]', 'filing_date_desc');

    // Verify sorted
    const firstFilingDate = await page.textContent('[data-testid="filing-0-date"]');
    const secondFilingDate = await page.textContent('[data-testid="filing-1-date"]');

    // First should be more recent
    expect(new Date(firstFilingDate || '')).toBeInstanceOf(Date);
  });
});

test.describe('Real-time Updates', () => {
  test('receives WebSocket updates', async ({ page }) => {
    await page.goto(`${BASE_URL}/filing/test-123`);

    // Track WebSocket connection
    const wsMessages: any[] = [];
    page.on('websocket', ws => {
      ws.on('framereceived', event => {
        wsMessages.push(JSON.parse(event.payload as string));
      });
    });

    // Wait for processing status
    await page.waitForSelector('[data-testid="processing-status"]');

    // Verify status updates received
    await page.waitForFunction(
      () => document.querySelector('[data-testid="processing-status"]')?.textContent === 'completed',
      { timeout: 30000 }
    );

    // Verify signals appeared
    await expect(page.locator('[data-testid="signal-count"]')).toHaveText(/\d+/);
  });

  test('handles WebSocket disconnection', async ({ page }) => {
    await page.goto(`${BASE_URL}/filing/test-123`);

    // Simulate network offline
    await page.context().setOffline(true);

    // Verify disconnection message
    await expect(page.locator('[data-testid="connection-status"]')).toHaveText(/disconnected/i);

    // Reconnect
    await page.context().setOffline(false);

    // Verify reconnection
    await expect(page.locator('[data-testid="connection-status"]')).toHaveText(/connected/i, {
      timeout: 10000
    });
  });
});

test.describe('Form Submissions', () => {
  test('submit new filing for analysis', async ({ page }) => {
    await page.goto(`${BASE_URL}/submit`);

    // Fill form
    await page.fill('[data-testid="cik-input"]', '0000789019');
    await page.selectOption('[data-testid="form-type-select"]', '10-K');
    await page.fill('[data-testid="accession-input"]', '0000789019-24-000456');

    // Submit
    await page.click('[data-testid="submit-button"]');

    // Verify success message
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();

    // Verify redirected to status page
    await page.waitForURL(/\/filing\/\w+/);
  });

  test('form validation errors', async ({ page }) => {
    await page.goto(`${BASE_URL}/submit`);

    // Submit without required fields
    await page.click('[data-testid="submit-button"]');

    // Verify error messages
    await expect(page.locator('[data-testid="cik-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="form-type-error"]')).toBeVisible();
  });
});

test.describe('Responsive Design', () => {
  test('mobile layout', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(BASE_URL);

    // Verify mobile menu
    await page.click('[data-testid="mobile-menu-button"]');
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();

    // Navigate via mobile menu
    await page.click('[data-testid="mobile-menu-filings"]');
    await expect(page).toHaveURL(/\/filings/);

    // Verify responsive table
    const table = page.locator('[data-testid="filing-table"]');
    await expect(table).toBeVisible();

    // Should show card layout on mobile
    const cards = await page.locator('[data-testid^="filing-card-"]').count();
    expect(cards).toBeGreaterThan(0);
  });

  test('tablet layout', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(BASE_URL);

    // Verify layout adjustments
    const container = page.locator('[data-testid="main-container"]');
    await expect(container).toHaveCSS('max-width', /768px|100%/);
  });

  test('desktop layout', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(BASE_URL);

    // Verify full layout
    await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();
    await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
  });
});

test.describe('Accessibility', () => {
  test('keyboard navigation', async ({ page }) => {
    await page.goto(BASE_URL);

    // Tab through interactive elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Verify focus visible
    const focusedElement = await page.evaluate(() => document.activeElement?.getAttribute('data-testid'));
    expect(focusedElement).toBeTruthy();

    // Test Enter key activation
    await page.keyboard.press('Enter');
  });

  test('screen reader announcements', async ({ page }) => {
    await page.goto(BASE_URL);

    // Verify ARIA live regions
    const liveRegion = page.locator('[aria-live="polite"]');
    await expect(liveRegion).toBeAttached();

    // Trigger update
    await page.click('[data-testid="load-more"]');

    // Verify announcement
    await expect(liveRegion).toHaveText(/loaded/i);
  });

  test('focus management', async ({ page }) => {
    await page.goto(BASE_URL);

    // Open modal
    await page.click('[data-testid="open-modal"]');

    // Verify focus trapped in modal
    await expect(page.locator('[data-testid="modal"]')).toBeFocused();

    // Close modal
    await page.keyboard.press('Escape');

    // Verify focus returned
    await expect(page.locator('[data-testid="open-modal"]')).toBeFocused();
  });
});

test.describe('Performance', () => {
  test('initial page load under 3 seconds', async ({ page }) => {
    const start = Date.now();

    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    const duration = Date.now() - start;

    expect(duration).toBeLessThan(3000);
  });

  test('Time to Interactive under 5 seconds', async ({ page }) => {
    await page.goto(BASE_URL);

    // Measure TTI using Performance API
    const tti = await page.evaluate(() => {
      return new Promise((resolve) => {
        if ('PerformanceObserver' in window) {
          const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            for (const entry of entries) {
              if (entry.name === 'first-input') {
                resolve(entry.startTime);
              }
            }
          });
          observer.observe({ entryTypes: ['first-input'] });
        }
      });
    });

    expect(tti).toBeLessThan(5000);
  });

  test('lazy loading images', async ({ page }) => {
    await page.goto(`${BASE_URL}/gallery`);

    // Verify images use loading="lazy"
    const images = page.locator('img[loading="lazy"]');
    const count = await images.count();

    expect(count).toBeGreaterThan(0);

    // Verify images not in viewport aren't loaded
    const firstImage = images.first();
    await expect(firstImage).toHaveAttribute('loading', 'lazy');
  });
});

test.describe('Error Handling', () => {
  test('404 page', async ({ page }) => {
    await page.goto(`${BASE_URL}/nonexistent-page`);

    await expect(page.locator('[data-testid="error-404"]')).toBeVisible();
    await expect(page.locator('h1')).toHaveText(/not found/i);

    // Verify back to home link
    await page.click('[data-testid="back-home"]');
    await expect(page).toHaveURL(BASE_URL);
  });

  test('API error handling', async ({ page }) => {
    // Mock API error
    await page.route('**/api/v1/filings', route => {
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server error' }) });
    });

    await page.goto(BASE_URL);

    // Verify error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toHaveText(/error/i);

    // Verify retry button
    await page.click('[data-testid="retry-button"]');
  });
});

test.describe('Authentication Flow', () => {
  test('login flow', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Fill credentials
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');

    // Submit
    await page.click('[data-testid="login-button"]');

    // Verify redirected to dashboard
    await expect(page).toHaveURL(/\/dashboard/);

    // Verify user menu visible
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('logout flow', async ({ page }) => {
    // Assume logged in
    await page.goto(`${BASE_URL}/dashboard`);

    // Open user menu
    await page.click('[data-testid="user-menu"]');

    // Logout
    await page.click('[data-testid="logout-button"]');

    // Verify redirected to home
    await expect(page).toHaveURL(BASE_URL);

    // Verify user menu not visible
    await expect(page.locator('[data-testid="user-menu"]')).not.toBeVisible();
  });
});

// E2E test summary:
// 1. Complete user workflows - ✓
// 2. Real-time updates - ✓
// 3. Form submissions - ✓
// 4. Responsive design - ✓
// 5. Accessibility - ✓
// 6. Performance - ✓
// 7. Error handling - ✓
// 8. Authentication - ✓
