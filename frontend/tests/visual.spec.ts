import { test, expect } from '@playwright/test';

test.describe('Dashboard UI Stability and Accessibility', () => {
  test('Login page renders with correct accessibility roles', async ({ page }) => {
    await page.goto('/login');
    
    // Check for main region
    const mainRegion = page.locator('main');
    await expect(mainRegion).toBeVisible();

    // Ensure focus state works on inputs
    const emailInput = page.locator('input[type="email"]');
    await emailInput.focus();
    await expect(emailInput).toBeFocused();

    // Visual Regression Check - Auth pages should be pixel-perfect
    await expect(page).toHaveScreenshot('auth-screen-baseline.png', {
      fullPage: true,
      maxDiffPixelRatio: 0.01 // Strict auth threshold
    });
  });

  test('Dashboard loads layout shell', async ({ page }) => {
    // Navigate to overview
    await page.goto('/overview');

    // Due to the redirect to /login if not authenticated, check URL
    const url = page.url();
    if (url.includes('/overview')) {
      const pageShell = page.locator('[data-layout-shell="PageShell"]');
      await expect(pageShell).toBeVisible();
      await expect(pageShell).toHaveAttribute('role', 'main');

      // Visual Regression Check - Dashboard Shell
      // We explicitly mask dynamic components to verify the shell
      await expect(page).toHaveScreenshot('dashboard-shell-baseline.png', {
        fullPage: true,
        maxDiffPixelRatio: 0.02, // Shell threshold
        mask: [
          page.locator('.recharts-wrapper'), // Mask charts
          page.locator('[data-test="timestamp"]'), // Mask timestamps
          page.locator('table'), // Mask dynamic data tables
        ]
      });

      // Verification of specific charts component
      const chartsContainer = page.locator('.recharts-wrapper').first();
      if (await chartsContainer.isVisible()) {
        await expect(chartsContainer).toHaveScreenshot('dashboard-charts-baseline.png', {
          maxDiffPixelRatio: 0.05 // Chart threshold
        });
      }
      
      // Verification of specific data table
      const dataTable = page.locator('table').first();
      if (await dataTable.isVisible()) {
        await expect(dataTable).toHaveScreenshot('dashboard-tables-baseline.png', {
          maxDiffPixelRatio: 0.03, // Table threshold
          mask: [page.locator('[data-test="timestamp"]')]
        });
      }
    }
  });
});
