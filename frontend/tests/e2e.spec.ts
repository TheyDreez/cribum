import { test, expect, Page } from '@playwright/test';

test.describe.serial('CRIBUM E2E Browser Test Suite — Operational Scenarios & Integrity', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    page.on('console', (msg) => console.log('BROWSER CONSOLE:', msg.text()));
    page.on('pageerror', (err) => console.log('BROWSER PAGE ERROR:', err.message));
    page.on('requestfailed', (req) => console.log('FAILED REQUEST:', req.url(), req.failure()?.errorText));

    await page.goto('/');
    await expect(page.locator('text=Fila de Auditoria')).toBeVisible({ timeout: 20000 });
    await expect(page.locator('aside div.overflow-y-auto button').first()).toBeVisible({ timeout: 20000 });
  });

  test.afterAll(async () => {
    await page?.close();
  });

  // Cenário 1: Selecionar documento na fila e verificar document-workspace isolado
  test('Cenário 01: Selecionar documento na fila e verificar document-workspace', async () => {
    const firstDoc = page.locator('aside div.overflow-y-auto button').first();
    await expect(firstDoc).toBeVisible();
    await firstDoc.click();

    const workspace = page.getByTestId('document-workspace');
    await expect(workspace).toBeVisible({ timeout: 10000 });

    const docImage = workspace.locator('img[alt="Guia Médica Original"]');
    await expect(docImage).toBeVisible({ timeout: 10000 });
    await expect(docImage).toHaveAttribute('src', /\/api\/documents\/.*\/image/);

    await expect(workspace.locator('text=Hipóteses de Leitura do VLM')).toBeVisible();
    await expect(workspace.locator('text=Parecer do Auditor Humano (HITL)')).toBeVisible();
  });

  // Cenário 2: Clicar em alerta/evidência e verificar destaque da bounding box SVG
  test('Cenário 02: Clicar em alerta/evidência e verificar destaque da bounding box SVG', async () => {
    const caso01 = page.locator('aside button', { hasText: 'Caso 01' }).first();
    await expect(caso01).toBeVisible();
    await caso01.click();

    const workspace = page.getByTestId('document-workspace');
    await expect(workspace.locator('img[alt="Guia Médica Original"]')).toBeVisible({ timeout: 10000 });

    // No Caso 01, o primeiro alerta já carrega selecionado com destaque pericial em tom âmbar (#b45309)
    const highlightedRect = workspace.locator('svg rect[stroke="#b45309"]');
    await expect(highlightedRect.first()).toBeVisible({ timeout: 5000 });
  });

  // Cenário 3: Selecionar hipótese no radio button
  test('Cenário 03: Selecionar hipótese no radio button e refletir no formulário', async () => {
    const caso01 = page.locator('aside button', { hasText: 'Caso 01' }).first();
    await caso01.click();

    const workspace = page.getByTestId('document-workspace');
    await expect(workspace.locator('text=Hipóteses de Leitura do VLM')).toBeVisible();

    const firstRadioLabel = workspace.locator('label:has(input[type="radio"])').first();
    await expect(firstRadioLabel).toBeVisible();
    await firstRadioLabel.click();

    const firstRadio = workspace.locator('input[type="radio"]').first();
    await expect(firstRadio).toBeChecked();

    const radioVal = await firstRadio.inputValue();
    const confirmedValBox = workspace.locator('text=Hipótese a confirmar:').locator('..');
    await expect(confirmedValBox).toContainText(radioVal);
  });

  // Cenário 4: Trocar de documento e verificar se o formulário limpa
  test('Cenário 04: Trocar de documento e verificar limpeza rigorosa do formulário HITL', async () => {
    const caso01 = page.locator('aside button', { hasText: 'Caso 01' }).first();
    await caso01.click();

    const workspace = page.getByTestId('document-workspace');
    await expect(workspace.locator('text=Hipóteses de Leitura do VLM')).toBeVisible();

    // Preenche justificativa no Caso 01
    const textarea = workspace.locator('textarea[placeholder*="Descreva a fundamentação"]');
    await textarea.fill('Justificativa temporária Caso 01');
    await expect(textarea).toHaveValue('Justificativa temporária Caso 01');

    // Troca para o Caso 06
    const caso06 = page.locator('aside button', { hasText: 'Caso 06' }).first();
    await expect(caso06).toBeVisible();
    await caso06.click();

    const workspace06 = page.getByTestId('document-workspace');
    const textarea06 = workspace06.locator('textarea[placeholder*="Descreva a fundamentação"]');
    await expect(textarea06).toHaveValue('');
  });

  // Cenário 5: Tentar confirmar sem hipótese válida e verificar impedimento
  test('Cenário 05: Impedimento de confirmação quando nenhuma hipótese for selecionada', async () => {
    const caso01 = page.locator('aside button', { hasText: 'Caso 01' }).first();
    await caso01.click();

    const workspace = page.getByTestId('document-workspace');
    await expect(workspace.locator('text=Hipóteses de Leitura do VLM')).toBeVisible();

    const actionSelect = workspace.locator('select');
    await actionSelect.selectOption('CONFIRMED_HYPOTHESIS');

    const textarea = workspace.locator('textarea[placeholder*="Descreva a fundamentação"]');
    await textarea.fill('Tentativa sem marcar hipótese');

    const submitBtn = workspace.locator('button', { hasText: 'Registrar revisão' });
    await expect(submitBtn).toBeDisabled();
    await expect(workspace.locator('text=Selecione uma das opções acima nas hipóteses')).toBeVisible();
  });

  // Cenário 6: Submeter hipótese confirmada e verificar persistência após reload
  test('Cenário 06: Submeter hipótese confirmada e verificar persistência no banco após reload', async () => {
    const caso01 = page.locator('aside button', { hasText: 'Caso 01' }).first();
    await caso01.click();

    const workspace = page.getByTestId('document-workspace');
    await expect(workspace.locator('text=Hipóteses de Leitura do VLM')).toBeVisible();

    const radioLabel = workspace.locator('label:has(input[type="radio"])').first();
    await radioLabel.click();

    const radio = workspace.locator('input[type="radio"]').first();
    const val = await radio.inputValue();

    const testReason = `Auditoria pericial confirmada: ${Date.now()}`;
    const textarea = workspace.locator('textarea[placeholder*="Descreva a fundamentação"]');
    await textarea.fill(testReason);

    const submitBtn = workspace.locator('button', { hasText: 'Registrar revisão' });
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();

    await expect(workspace.getByText(testReason).first()).toBeVisible({ timeout: 5000 });
    await expect(workspace.locator(`text=Valor: ${val}`).first()).toBeVisible();

    await page.reload();
    await expect(page.locator('text=Fila de Auditoria')).toBeVisible({ timeout: 15000 });

    const caso01Reloaded = page.locator('aside button', { hasText: 'Caso 01' }).first();
    await expect(caso01Reloaded).toBeVisible();
    await caso01Reloaded.click();

    const workspaceReloaded = page.getByTestId('document-workspace');
    await expect(workspaceReloaded.getByText(testReason).first()).toBeVisible({ timeout: 5000 });
  });

  // Cenário 7: Badges de status de revisão
  test('Cenário 07: Badges de status de revisão na fila documental', async () => {
    const pendenteBadges = page.locator('aside span', { hasText: 'Pendente' });
    expect(await pendenteBadges.count()).toBeGreaterThan(0);

    const caso01 = page.locator('aside button', { hasText: 'Caso 01' }).first();
    await expect(caso01.locator('span', { hasText: 'Em Revisão' })).toBeVisible();
  });

  // Cenário 8: Concorrência com atraso controlado (não mistura A com B)
  test('Cenário 08: Não mistura A com B quando A responde atrasado (intercepção controlada)', async () => {
    const docA = 'CASE-AMB-001';
    const docB = 'CASE-INC-006';

    // Primeiro garante que estamos no Caso 06
    await page.locator('aside button', { hasText: 'Caso 06' }).first().click();
    await expect(page.getByTestId('document-workspace')).toHaveAttribute('data-document-id', docB);

    let releaseA: (() => void) | undefined;
    let notifyAStarted: (() => void) | undefined;

    const aStarted = new Promise<void>((resolve) => {
      notifyAStarted = resolve;
    });

    const aGate = new Promise<void>((resolve) => {
      releaseA = resolve;
    });

    // Intercepta requisições ao documento A para atrasar artificialmente
    await page.route(`**/api/documents/${docA}`, async (route) => {
      const response = await route.fetch();
      notifyAStarted?.();
      await aGate;

      try {
        await route.fulfill({ response });
      } catch {
        // Abort de A é comportamento esperado
      }
    });

    try {
      // Clica em Caso 01 (dispara requisição de A)
      await page.locator('aside button', { hasText: 'Caso 01' }).first().click();

      // Espera a requisição de A ter chegado no interceptador
      await aStarted;

      // Imediatamente clica em Caso 06 antes de A responder
      await page.locator('aside button', { hasText: 'Caso 06' }).first().click();

      const workspace = page.getByTestId('document-workspace');
      await expect(workspace).toHaveAttribute('data-document-id', docB);

      await expect(
        workspace.locator('img[alt="Guia Médica Original"]'),
      ).toHaveAttribute('src', `/api/documents/${docB}/image`);

      await expect(workspace).toContainText('DOC-002-MISSING-CRM');
      await expect(workspace).not.toContainText('MED-001-AMBIGUOUS-READING');

      // Agora libera a resposta atrasada de A
      releaseA?.();

      // O workspace DEVE continuar sendo estritamente B
      await expect(workspace).toHaveAttribute('data-document-id', docB);
      await expect(workspace).toContainText('DOC-002-MISSING-CRM');
      await expect(workspace).not.toContainText('MED-001-AMBIGUOUS-READING');
    } finally {
      releaseA?.();
      await page.unroute(`**/api/documents/${docA}`);
    }
  });

  // Cenário 9: HTTP 400 e HTTP 500 preservam justificativa digitada
  test('Cenário 09: Erros HTTP 400 e 500 exibem alerta e preservam a justificativa digitada', async () => {
    const caso06 = page.locator('aside button', { hasText: 'Caso 06' }).first();
    await caso06.click();

    const workspace = page.getByTestId('document-workspace');
    const textarea = workspace.locator('textarea[placeholder*="Descreva a fundamentação"]');
    const typedReason = 'Justificativa crítica que não pode ser perdida em erro';
    await textarea.fill(typedReason);

    // 1. Simula HTTP 400 na submissão da revisão
    await page.route('**/api/documents/**/reviews', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Regra de negócio violada no teste 400.' }),
      });
    });

    try {
      const select = workspace.locator('select');
      await select.selectOption('REJECTED_CLAIM');

      const submitBtn = workspace.locator('button', { hasText: 'Registrar revisão' });
      await expect(submitBtn).toBeEnabled();
      await submitBtn.click();

      // Alerta de erro deve ser exibido com role="alert"
      const alertBox = workspace.locator('[role="alert"]');
      await expect(alertBox).toBeVisible({ timeout: 5000 });
      await expect(alertBox).toContainText('Regra de negócio violada no teste 400.');

      // O texto digitado DEVE permanecer inalterado no formulário!
      await expect(textarea).toHaveValue(typedReason);
    } finally {
      await page.unroute('**/api/documents/**/reviews');
    }

    // 2. Simula HTTP 500 na submissão da revisão
    await page.route('**/api/documents/**/reviews', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Falha interna de banco simulada.' }),
      });
    });

    try {
      const submitBtn = workspace.locator('button', { hasText: 'Registrar revisão' });
      await submitBtn.click();

      const alertBox = workspace.locator('[role="alert"]');
      await expect(alertBox).toBeVisible({ timeout: 5000 });
      await expect(alertBox).toContainText('Falha interna de banco simulada.');

      // O texto digitado CONTINUA preservado
      await expect(textarea).toHaveValue(typedReason);
    } finally {
      await page.unroute('**/api/documents/**/reviews');
    }
  });

  // Cenário 10: Justificativa com menos de 3 caracteres não habilita envio
  test('Cenário 10: Justificativa com menos de 3 caracteres não habilita envio', async () => {
    const caso06 = page.locator('aside button', { hasText: 'Caso 06' }).first();
    await caso06.click();

    const workspace = page.getByTestId('document-workspace');
    const select = workspace.locator('select');
    await select.selectOption('REJECTED_CLAIM');

    const textarea = workspace.locator('textarea[placeholder*="Descreva a fundamentação"]');
    const submitBtn = workspace.locator('button', { hasText: 'Registrar revisão' });

    // 2 caracteres: desabilitado
    await textarea.fill('ab');
    await expect(submitBtn).toBeDisabled();

    // Apenas espaços: desabilitado
    await textarea.fill('    ');
    await expect(submitBtn).toBeDisabled();

    // 3 caracteres úteis: habilitado
    await textarea.fill('abc');
    await expect(submitBtn).toBeEnabled();
  });

  // Cenário 11: Recolher painéis é real, tem aria-expanded e preserva formulário
  test('Cenário 11: Painéis retráteis preservam estado e atualizam aria-expanded', async () => {
    const workspace = page.getByTestId('document-workspace');
    const textarea = workspace.locator('textarea[placeholder*="Descreva a fundamentação"]');
    const preservedText = 'Texto preenchido antes de recolher o painel';
    await textarea.fill(preservedText);

    // Botão de recolher revisão
    const toggleReviewBtn = page.locator('button', { hasText: 'Ocultar revisão' });
    await expect(toggleReviewBtn).toHaveAttribute('aria-expanded', 'true');
    await toggleReviewBtn.click();

    // Agora o botão deve indicar "Mostrar revisão" e aria-expanded="false"
    const showReviewBtn = page.locator('button', { hasText: 'Mostrar revisão' });
    await expect(showReviewBtn).toHaveAttribute('aria-expanded', 'false');

    // Ao reabrir, o texto digitado DEVE continuar exatamente o mesmo
    await showReviewBtn.click();
    await expect(page.locator('button', { hasText: 'Ocultar revisão' })).toHaveAttribute('aria-expanded', 'true');
    await expect(textarea).toHaveValue(preservedText);

    // Botão de recolher fila
    const toggleQueueBtn = page.locator('button', { hasText: 'Ocultar fila' });
    await expect(toggleQueueBtn).toHaveAttribute('aria-expanded', 'true');
    await toggleQueueBtn.click();

    const showQueueBtn = page.locator('button', { hasText: 'Mostrar fila' });
    await expect(showQueueBtn).toHaveAttribute('aria-expanded', 'false');

    await showQueueBtn.click();
    await expect(page.locator('button', { hasText: 'Ocultar fila' })).toHaveAttribute('aria-expanded', 'true');
  });

  // Cenário 12: Controles de Zoom e alinhamento
  test('Cenário 12: Controles de zoom pericial (largura, página, manual e reset)', async () => {
    const workspace = page.getByTestId('document-workspace');

    // Clica em Ajustar à largura
    const fitWidthBtn = workspace.locator('button', { hasText: 'Ajustar à largura' });
    await fitWidthBtn.click();

    // Clica em Ajustar à página
    const fitPageBtn = workspace.locator('button', { hasText: 'Ajustar à página' });
    await fitPageBtn.click();

    // Zoom manual In
    const zoomInBtn = workspace.locator('button[title*="Aumentar zoom"]');
    await zoomInBtn.click();

    // Reset 100%
    const resetBtn = workspace.locator('button[title*="Redefinir visualização"]');
    await resetBtn.click();

    // O indicador deve mostrar 100%
    await expect(workspace.locator('span[title*="Clique para redefinir"]')).toHaveText('100%');
  });

  // Cenário 13: Rede de Guias (Grafo) e seleção de anomalias
  test('Cenário 13: Rede de Guias e seleção de anomalias relacionais', async () => {
    const redeTab = page.locator('button', { hasText: 'Rede de Guias (Grafo)' });
    await redeTab.click();

    await expect(page.locator('text=Grafo Relacional Multi-Entidade')).toBeVisible();
    await expect(page.locator('text=Limites Probatórios do Grafo de Relações')).toBeVisible();

    const anomalyCards = page.locator('div.w-96 div.cursor-pointer');
    await expect(anomalyCards.first()).toBeVisible({ timeout: 5000 });

    await anomalyCards.nth(0).click();
    await anomalyCards.nth(1).click();

    // Retorna para auditoria
    const auditTab = page.locator('button', { hasText: 'Auditoria Individual' });
    await auditTab.click();
    await expect(page.locator('text=Fila de Auditoria')).toBeVisible();
  });

  // Cenário 14: Inferência REAL falha explicitamente sem fallback silencioso
  test('Cenário 14: Inferência REAL sem infraestrutura falha com 503 INFERENCE_UNAVAILABLE', async () => {
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
