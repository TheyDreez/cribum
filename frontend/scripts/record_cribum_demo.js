import { chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';

async function record() {
  const framesDir = 'C:/Users/andre/.gemini/antigravity/scratch/portfolio_test/gif_frames';
  if (!fs.existsSync(framesDir)) {
    fs.mkdirSync(framesDir, { recursive: true });
  } else {
    const files = fs.readdirSync(framesDir);
    for (const f of files) {
      fs.unlinkSync(path.join(framesDir, f));
    }
  }

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

  const page = await browser.newPage({
    viewport: { width: 1440, height: 810 },
    deviceScaleFactor: 1,
  });

  let frameIdx = 0;
  async function snap(count = 1, delay = 100) {
    for (let i = 0; i < count; i++) {
      const p = path.join(framesDir, `frame_${String(frameIdx).padStart(4, '0')}.png`);
      await page.screenshot({ path: p });
      frameIdx++;
      if (delay > 0) await page.waitForTimeout(delay);
    }
  }

  for (let attempt = 0; attempt < 5; attempt++) {
    try {
      await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle', timeout: 15000 });
      break;
    } catch (e) {
      if (attempt === 4) throw e;
      await new Promise(r => setTimeout(r, 1000));
    }
  }
  await page.waitForSelector('#document-queue', { timeout: 15000 });
  await page.waitForTimeout(1000);

  // Filter "Com Alertas"
  const alertFilter = page.locator('button', { hasText: 'Com Alertas' });
  if (await alertFilter.isVisible()) {
    await alertFilter.click();
    await page.waitForTimeout(400);
  }

  // Select Caso 01
  const caso01 = page.locator('button', { hasText: 'Caso 01' }).first();
  if (await caso01.isVisible()) {
    await caso01.click();
    await page.waitForTimeout(800);
  }

  // Select LASA finding to highlight
  const lasaCard = page.locator('div', { hasText: 'Risco Crítico de Troca LASA' }).first();
  if (await lasaCard.isVisible()) {
    await lasaCard.click();
    await page.waitForTimeout(500);
  }

  // Initial dashboard view (2 seconds)
  await snap(10, 150);

  // 1. Contraste Dinâmico
  const contrastBtn = page.locator('[data-testid="filter-contrast"]');
  if (await contrastBtn.isVisible()) {
    await contrastBtn.click();
    await page.waitForTimeout(200);
    await snap(6, 150);
  }

  // 2. Negativo Forense
  const invertBtn = page.locator('[data-testid="filter-invert"]');
  if (await invertBtn.isVisible()) {
    await invertBtn.click();
    await page.waitForTimeout(200);
    await snap(6, 150);
  }

  // 3. Realce de Tinta
  const inkBtn = page.locator('[data-testid="filter-ink"]');
  if (await inkBtn.isVisible()) {
    await inkBtn.click();
    await page.waitForTimeout(200);
    await snap(6, 150);
  }

  // 4. Return to Original
  const origBtn = page.locator('[data-testid="filter-none"]').or(page.locator('button', { hasText: 'Original' })).first();
  if (await origBtn.isVisible()) {
    await origBtn.click();
    await page.waitForTimeout(200);
    await snap(5, 150);
  }

  // 5. Open Forensic Report
  const reportBtn = page.locator('[data-testid="export-forensic-report-btn"]');
  if (await reportBtn.isVisible()) {
    await reportBtn.click();
    await page.waitForTimeout(500);
    await snap(10, 200);

    const closeBtn = page.locator('[data-testid="close-report-btn"]');
    if (await closeBtn.isVisible()) {
      await closeBtn.click();
    } else {
      await page.keyboard.press('Escape');
    }
    await page.waitForTimeout(300);
    await snap(4, 150);
  }

  // 6. Switch to Network Graph
  const redeTab = page.locator('button', { hasText: 'Rede de Guias' }).first();
  if (await redeTab.isVisible()) {
    await redeTab.click();
    await page.waitForTimeout(800);
    await snap(12, 200);
  }

  // 7. Back to Auditoria Individual
  const auditTab = page.locator('button', { hasText: 'Auditoria Individual' }).first();
  if (await auditTab.isVisible()) {
    await auditTab.click();
    await page.waitForTimeout(500);
    await snap(6, 150);
  }

  await browser.close();
  console.log(`Successfully recorded ${frameIdx} frames!`);
}

record().catch((e) => {
  console.error(e);
  process.exit(1);
});
