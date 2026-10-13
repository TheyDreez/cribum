import { chromium } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function capture() {
  const browser = await chromium.launch({ headless: true });

  const viewports = [
    { name: 'notebook_1366x768', width: 1366, height: 768, dpr: 1 },
    { name: 'desktop_1920x1080', width: 1920, height: 1080, dpr: 1 },
    { name: 'wide_2560x1440', width: 2560, height: 1440, dpr: 1 },
  ];

  const outputDir = path.resolve(__dirname, '../docs/screenshots/baseline');

  for (const vp of viewports) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: vp.dpr,
    });
    const page = await context.newPage();
    await page.goto('http://127.0.0.1:5173/');
    await page.waitForSelector('img[alt="Guia Médica Original"]', { timeout: 15000 });
    // Wait a moment for layout stabilization
    await page.waitForTimeout(1000);

    const shotPath = path.join(outputDir, `${vp.name}.png`);
    await page.screenshot({ path: shotPath, fullPage: false });
    console.log(`Saved baseline screenshot: ${shotPath} (viewport: ${vp.width}x${vp.height})`);

    // Also take a screenshot of Network Graph view
    const redeTab = page.locator('button', { hasText: 'Rede de Guias (Grafo)' });
    if (await redeTab.isVisible()) {
      await redeTab.click();
      await page.waitForTimeout(1000);
      const graphShotPath = path.join(outputDir, `${vp.name}_graph.png`);
      await page.screenshot({ path: graphShotPath, fullPage: false });
      console.log(`Saved baseline graph screenshot: ${graphShotPath}`);
    }

    await context.close();
  }

  await browser.close();
}

capture().catch((err) => {
  console.error(err);
  process.exit(1);
});
