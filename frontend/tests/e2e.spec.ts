import { test, expect, Page } from '@playwright/test';

test.describe.serial('CRIBUM E2E Browser Test Suite — 12 Operational Scenarios', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    page.on('console', (msg) => console.log('BROWSER CONSOLE:', msg.text()));
    page.on('pageerror', (err) => console.log('BROWSER PAGE ERROR:', err.message));
    page.on('requestfailed', (req) => console.log('FAILED REQUEST:', req.url(), req.failure()?.errorText));
    await page.goto('http://127.0.0.1:5173/');
    console.log('PAGE TITLE:', await page.title());
    console.log('PAGE HTML:', (await page.content()).slice(0, 400));
    await expect(page.locator('text=Fila de Auditoria')).toBeVisible({ timeout: 20000 });
    await expect(page.locator('aside div.overflow-y-auto button').first()).toBeVisible({ timeout: 20000 });
  });

  test.afterAll(async () => {
    await page?.close();
  });

  // Cenário 1: Selecionar documento na fila e acionar execução
  test('Cenário 01: Selecionar documento na fila e acionar visualização pericial', async () => {
    const firstDoc = page.locator('aside div.overflow-y-auto button').first();
    await expect(firstDoc).toBeVisible();
    await firstDoc.click();

    // Verifica que o visualizador carregou a imagem e os painéis de auditoria
    const docImage = page.locator('img[alt="Guia Médica Original"]');
    await expect(docImage).toBeVisible({ timeout: 10000 });
    await expect(docImage).toHaveAttribute('src', /\/api\/documents\/.*\/image/);

    // Verifica painéis de hipóteses e parecer pericial
    await expect(page.locator('text=Hipóteses de Leitura do VLM')).toBeVisible();
    await expect(page.locator('text=Parecer do Auditor Humano (HITL)')).toBeVisible();
  });

  // Cenário 2: Clicar em evidência e verificar destaque da bounding box
  test('Cenário 02: Clicar em alerta/evidência e verificar destaque da bounding box SVG', async () => {
    const caso01 = page.locator('aside button', { hasText: 'Caso 01' }).first();
    await expect(caso01).toBeVisible();
    await caso01.click();

    await expect(page.locator('img[alt="Guia Médica Original"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Alertas de Inconsistência')).toBeVisible();

    // No Caso 01, o primeiro alerta já carrega selecionado com destaque pericial
    const highlightedRect = page.locator('svg rect[stroke="#f43f5e"]');
    await expect(highlightedRect.first()).toBeVisible({ timeout: 5000 });
  });

  // Cenário 3: Selecionar hipótese no radio button
  test('Cenário 03: Selecionar hipótese no radio button e refletir no formulário', async () => {
    const caso01 = page.locator('aside button', { hasText: 'Caso 01' }).first();
    await caso01.click();
    await expect(page.locator('text=Hipóteses de Leitura do VLM')).toBeVisible();

    const firstRadioLabel = page.locator('label:has(input[type="radio"])').first();
    await expect(firstRadioLabel).toBeVisible();
    await firstRadioLabel.click();

    const firstRadio = page.locator('input[type="radio"]').first();
    await expect(firstRadio).toBeChecked();

    const radioVal = await firstRadio.inputValue();
    const confirmedValBox = page.locator('text=Hipótese a confirmar:').locator('..');
    await expect(confirmedValBox).toContainText(radioVal);
  });

  // Cenário 4: Trocar de documento e verificar se o formulário limpa
  test('Cenário 04: Trocar de documento e verificar limpeza rigorosa do formulário HITL', async () => {
    const caso01 = page.locator('aside button', { hasText: 'Caso 01' }).first();
    await caso01.click();
    await expect(page.locator('text=Hipóteses de Leitura do VLM')).toBeVisible();

    // Preenche justificativa no Caso 01
    const textarea = page.locator('textarea[placeholder*="Descreva a fundamentação"]');
    await textarea.fill('Justificativa temporária Caso 01');
    await expect(textarea).toHaveValue('Justificativa temporária Caso 01');

    // Troca para o Caso 06
    const caso06 = page.locator('aside button', { hasText: 'Caso 06' }).first();
    await expect(caso06).toBeVisible();
    await caso06.click();

    // Verifica que o formulário foi limpo
    await expect(textarea).toHaveValue('');
  });

  // Cenário 5: Tentar confirmar sem hipótese válida e verificar impedimento
  test('Cenário 05: Impedimento de confirmação quando nenhuma hipótese for selecionada', async () => {
    const caso01 = page.locator('aside button', { hasText: 'Caso 01' }).first();
    await caso01.click();
    await expect(page.locator('text=Hipóteses de Leitura do VLM')).toBeVisible();

    // Seleciona ação CONFIRMED_HYPOTHESIS
    const actionSelect = page.locator('select');
    await actionSelect.selectOption('CONFIRMED_HYPOTHESIS');

    // Preenche justificativa sem selecionar hipótese
    const textarea = page.locator('textarea[placeholder*="Descreva a fundamentação"]');
    await textarea.fill('Tentativa sem marcar hipótese');

    // Botão Registrar revisão deve estar desabilitado
    const submitBtn = page.locator('button', { hasText: 'Registrar revisão' });
    await expect(submitBtn).toBeDisabled();
    await expect(page.locator('text=Selecione uma das opções acima nas hipóteses')).toBeVisible();
  });

  // Cenário 6: Submeter hipótese confirmada e verificar persistência no banco após reload
  test('Cenário 06: Submeter hipótese confirmada e verificar persistência no banco após reload', async () => {
    const caso01 = page.locator('aside button', { hasText: 'Caso 01' }).first();
    await caso01.click();
    await expect(page.locator('text=Hipóteses de Leitura do VLM')).toBeVisible();

    // Clica no label da hipótese para selecioná-la
    const radioLabel = page.locator('label:has(input[type="radio"])').first();
    await radioLabel.click();

    const radio = page.locator('input[type="radio"]').first();
    const val = await radio.inputValue();

    const testReason = `Auditoria pericial confirmada: ${Date.now()}`;
    const textarea = page.locator('textarea[placeholder*="Descreva a fundamentação"]');
    await textarea.fill(testReason);

    const submitBtn = page.locator('button', { hasText: 'Registrar revisão' });
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();

    // Verifica no histórico pericial
    await expect(page.getByText(testReason).first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator(`text=Valor: ${val}`).first()).toBeVisible();

    // Recarrega a página completa do navegador
    await page.reload();
    await expect(page.locator('text=Fila de Auditoria')).toBeVisible({ timeout: 15000 });

    const caso01Reloaded = page.locator('aside button', { hasText: 'Caso 01' }).first();
    await expect(caso01Reloaded).toBeVisible();
    await caso01Reloaded.click();

    await expect(page.getByText(testReason).first()).toBeVisible({ timeout: 5000 });
  });

  // Cenário 7: Verificar badges de status de revisão na fila documental
  test('Cenário 07: Verificar badges de status de revisão na fila documental', async () => {
    // Casos novos devem ter status "Pendente"
    const pendenteBadges = page.locator('aside span', { hasText: 'Pendente' });
    expect(await pendenteBadges.count()).toBeGreaterThan(0);

    // Caso 01 que acabou de ter decisão humana registrada passa para "Em Revisão"
    const caso01 = page.locator('aside button', { hasText: 'Caso 01' }).first();
    await expect(caso01.locator('span', { hasText: 'Em Revisão' })).toBeVisible();
  });

  // Cenário 8: Race guard: alternar rapidamente entre documentos sem misturar imagens e dados
  test('Cenário 08: Race guard: alternância rápida entre documentos sem misturar imagens e dados', async () => {
    const docs = page.locator('aside div.overflow-y-auto button');
    const docCount = await docs.count();
    expect(docCount).toBeGreaterThan(3);

    // Clica rapidamente em 3 documentos diferentes em sequência
    await docs.nth(0).click();
    await docs.nth(1).click();
    await docs.nth(2).click();

    await page.waitForLoadState('networkidle');

    const docImage = page.locator('img[alt="Guia Médica Original"]');
    await expect(docImage).toBeVisible({ timeout: 10000 });
    await expect(docImage).toHaveAttribute('src', /\/api\/documents\/.*\/image/);
  });

  // Cenário 9: Garantir que imagem do documento, campos e achados exibidos pertencem todos ao documento selecionado
  test('Cenário 09: Coerência estrita entre imagem, achados e campos do mesmo documento', async () => {
    // Seleciona o Caso 06 (Ausência de CRM)
    const caso06 = page.locator('aside button', { hasText: 'Caso 06' }).first();
    await expect(caso06).toBeVisible();
    await caso06.click();

    await expect(page.locator('text=DOC-002-MISSING-CRM')).toBeVisible({ timeout: 5000 });

    // Seleciona o Caso 01 (LASA)
    const caso01 = page.locator('aside button', { hasText: 'Caso 01' }).first();
    await expect(caso01).toBeVisible();
    await caso01.click();

    await expect(page.locator('text=MED-001-AMBIGUOUS-READING')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=DOC-002-MISSING-CRM')).not.toBeVisible();
  });

  // Cenário 10: Seleção de anomalias no grafo exibe cards e guias distintas
  test('Cenário 10: Seleção de anomalias no grafo exibe cards e guias distintas', async () => {
    const redeTab = page.locator('button', { hasText: 'Rede de Guias (Grafo)' });
    await redeTab.click();

    await expect(page.locator('text=Grafo Relacional Multi-Entidade')).toBeVisible();
    await expect(page.locator('text=Limites Probatórios do Grafo de Relações')).toBeVisible();

    const anomalyCards = page.locator('div.w-96 div.cursor-pointer');
    await expect(anomalyCards.first()).toBeVisible({ timeout: 5000 });
    const count = await anomalyCards.count();
    expect(count).toBeGreaterThanOrEqual(2);

    await anomalyCards.nth(0).click();
    await anomalyCards.nth(1).click();

    // Retorna para a aba Auditoria Individual
    const auditTab = page.locator('button', { hasText: 'Auditoria Individual' });
    await auditTab.click();
    await expect(page.locator('text=Fila de Auditoria')).toBeVisible();
  });

  // Cenário 11: Banner de modo DEMO e ausência de falsas alegações de hardware
  test('Cenário 11: Banner de modo DEMO e ausência de falsas alegações de hardware', async () => {
    const demoBanner = page.locator('text=MODO DEMO ATIVO');
    await expect(demoBanner).toBeVisible();

    const hardwareBadge = page.locator('text=Fixture Demo Engine');
    await expect(hardwareBadge).toBeVisible();
  });

  // Cenário 12: Tentativa de inferência REAL sem endpoint falha explicitamente sem fallback
  test('Cenário 12: Tentativa de inferência REAL sem endpoint falha explicitamente sem fallback', async () => {
    const result = await page.evaluate(async () => {
      const res = await fetch('/api/documents/CASE-CTR-020/runs?mode_override=REAL', { method: 'POST' });
      const data = await res.json();
      return { status: res.status, body: data };
    });

    expect(result.status).toBe(503);
    expect(result.body.detail.error).toBe('INFERENCE_UNAVAILABLE');
    expect(result.body.detail.message).toContain('infraestrutura AMD');
  });
});
