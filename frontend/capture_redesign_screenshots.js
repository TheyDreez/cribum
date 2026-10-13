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
      '--disable-features=IsolateOrigins,site-per-process',
    ],
  });

  const viewports = [
    { name: 'notebook_1366x768', width: 1366, height: 768, dpr: 1 },
    { name: 'desktop_1920x1080', width: 1920, height: 1080, dpr: 1 },
    { name: 'wide_2560x1440', width: 2560, height: 1440, dpr: 1 },
  ];

  const outputDir = path.resolve(__dirname, '../docs/screenshots/redesign');

  const context = await browser.newContext();
  const page = await context.newPage();

  for (const vp of viewports) {
    await page.setViewportSize({ width: vp.width, height: vp.height });
    await page.goto('http://127.0.0.1:5173/');
    await page.waitForSelector('img[alt="Guia Médica Original"]', { timeout: 15000 });

    // Select Caso 01 to show active findings, hypotheses, and bounding boxes
    const caso01 = page.locator('aside button', { hasText: 'Caso 01' }).first();
    if (await caso01.isVisible()) {
      await caso01.click();
    }
    await page.waitForTimeout(500);

    const shotPath = path.join(outputDir, `${vp.name}.png`);
    await page.screenshot({ path: shotPath, fullPage: false });
    console.log(`Saved redesign screenshot: ${shotPath} (viewport: ${vp.width}x${vp.height})`);

    // Also take a screenshot of Network Graph view
    const redeTab = page.locator('button', { hasText: 'Rede de Guias (Grafo)' });
    if (await redeTab.isVisible()) {
      await redeTab.click();
      await page.waitForTimeout(500);
      const graphShotPath = path.join(outputDir, `${vp.name}_graph.png`);
      await page.screenshot({ path: graphShotPath, fullPage: false });
      console.log(`Saved redesign graph screenshot: ${graphShotPath}`);
    }

    const auditTab = page.locator('button', { hasText: 'Auditoria Individual' });
    if (await auditTab.isVisible()) {
      await auditTab.click();
    }
  }

  await context.close();

  await browser.close();
}

capture().catch((err) => {
  console.error(err);
  process.exit(1);
});
