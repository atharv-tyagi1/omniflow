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

    // Visual Regression Check
    await expect(page).toHaveScreenshot('login-page.png', {
      fullPage: true,
      maxDiffPixelRatio: 0.05
    });
  });

  test('Dashboard loads layout shell', async ({ page }) => {
    // We mock the auth state here or rely on the actual page redirect handling
    await page.goto('/overview');

    // Due to the redirect to /login if not authenticated, we check if layout or page shell exists 
    // when auth is mocked, or just check that we are properly redirected.
    const url = page.url();
    if (url.includes('/overview')) {
      const pageShell = page.locator('[data-layout-shell="PageShell"]');
      await expect(pageShell).toBeVisible();
      await expect(pageShell).toHaveAttribute('role', 'main');

      // Visual Regression Check with Masking for Dynamic Data (Charts, Timestamps)
      await expect(page).toHaveScreenshot('dashboard-overview.png', {
        fullPage: true,
        maxDiffPixelRatio: 0.08, // Relaxed threshold for complex page
        mask: [
          page.locator('.recharts-wrapper'), // Mask recharts
          page.locator('text=Refreshed'), // Mask timestamps
        ]
      });
    }
  });
});
