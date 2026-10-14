import { chromium } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function capture() {
  const browser = await chromium.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-web-security',
      '--allow-running-insecure-content',
    ],
  });

  const viewports = [
    { name: 'vp_1440x900', width: 1440, height: 900, dpr: 1 },
    { name: 'vp_1440x900_2x', width: 1440, height: 900, dpr: 2 },
    { name: 'vp_1600x900', width: 1600, height: 900, dpr: 1 },
    { name: 'vp_1920x1080', width: 1920, height: 1080, dpr: 1 },
  ];

  const outDir = 'C:/Users/andre/.gemini/antigravity/scratch/portfolio_test';

  for (const vp of viewports) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: vp.dpr,
    });
    const page = await context.newPage();

    await page.goto('http://127.0.0.1:5173/');
    await page.waitForSelector('img[alt="Guia Médica Original"]', { timeout: 15000 });

    // Select Caso 01
    const caso01 = page.locator('button', { hasText: 'Caso 01' }).first();
    if (await caso01.isVisible()) {
      await caso01.click();
    }
    await page.waitForTimeout(1000);

    const auditPath = path.join(outDir, `${vp.name}_audit.png`);
    await page.screenshot({ path: auditPath, fullPage: false });
    console.log(`Saved audit: ${auditPath}`);

    // Switch to graph tab
    const redeTab = page.locator('button', { hasText: 'Rede de Guias (Grafo)' });
    if (await redeTab.isVisible()) {
      await redeTab.click();
      await page.waitForTimeout(1200);

      const graphPath = path.join(outDir, `${vp.name}_graph.png`);
      await page.screenshot({ path: graphPath, fullPage: false });
      console.log(`Saved graph: ${graphPath}`);
    }

    await context.close();
  }

  await browser.close();
  console.log('Capture complete!');
}

capture().catch((err) => {
  console.error(err);
  process.exit(1);
});
