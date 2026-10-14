import { chromium } from '@playwright/test';
import path from 'path';

async function run() {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const viewports = [
    { name: '1600x900', width: 1600, height: 900, dpr: 1 },
    { name: '1920x1080', width: 1920, height: 1080, dpr: 1 },
    { name: '1440x900', width: 1440, height: 900, dpr: 1 },
  ];

  const outDir = 'C:/Users/andre/.gemini/antigravity/scratch/portfolio_test';

  for (const vp of viewports) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: vp.dpr,
    });
    const page = await context.newPage();
    await page.goto('http://127.0.0.1:5173/');
    await page.waitForTimeout(1000);

    // Filter by "Com Alertas"
    const alertFilter = page.locator('button', { hasText: 'Com Alertas' });
    if (await alertFilter.isVisible()) {
      await alertFilter.click();
      await page.waitForTimeout(400);
    }

    // Select Caso 01
    const caso01 = page.locator('button', { hasText: 'Caso 01' }).first();
    if (await caso01.isVisible()) {
      await caso01.click();
      await page.waitForTimeout(1000);
    }

    // Click on the LASA finding card in the right panel to focus on it
    const lasaCard = page.locator('div', { hasText: 'Risco Crítico de Troca LASA' }).first();
    if (await lasaCard.isVisible()) {
      await lasaCard.click();
      await page.waitForTimeout(600);
    }

    // Take screenshot of Audit Dashboard
    await page.screenshot({ path: path.join(outDir, `audit_${vp.name}.png`) });

    // Open Report Modal
    const reportBtn = page.locator('button', { hasText: 'Exportar Laudo' });
    if (await reportBtn.isVisible()) {
      await reportBtn.click();
      await page.waitForTimeout(600);
      await page.screenshot({ path: path.join(outDir, `report_modal_${vp.name}.png`) });

      // Close modal
      const closeBtn = page.locator('button', { hasText: 'Fechar' }).or(page.locator('button:has-text("✕")')).or(page.locator('button[aria-label="Close"]')).first();
      if (await closeBtn.isVisible()) {
        await closeBtn.click();
        await page.waitForTimeout(400);
      } else {
        await page.keyboard.press('Escape');
        await page.waitForTimeout(400);
      }
    }

    // Switch to Rede de Guias (Grafo)
    const redeTab = page.locator('button', { hasText: 'Rede de Guias (Grafo)' });
    if (await redeTab.isVisible()) {
      await redeTab.click();
      await page.waitForTimeout(1200);

      // Take screenshot of Graph view
      await page.screenshot({ path: path.join(outDir, `graph_${vp.name}.png`) });
    }

    await context.close();
  }

  await browser.close();
  console.log('All viewports rendered successfully!');
}

run().catch((e) => {
  console.error(e);
  process.exit(1);
});
