import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { DocumentQueue } from './components/DocumentQueue';
import { DocumentViewer } from './components/DocumentViewer';
import { FindingsPanel } from './components/FindingsPanel';
import { NetworkGraphView } from './components/NetworkGraphView';
import { ForensicReportModal } from './components/ForensicReportModal';
import { AppConfig, DocumentDetail, DocumentItem, Finding, ReviewSubmission } from './types';
import { PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen } from 'lucide-react';

function extractApiError(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== 'object') return fallback;

  const detail = (payload as { detail?: unknown }).detail;

  if (typeof detail === 'string') return detail;

  if (detail && typeof detail === 'object') {
    const message = (detail as { message?: unknown }).message;
    if (typeof message === 'string') return message;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item: unknown) => {
        if (!item || typeof item !== 'object') return '';
        const message = (item as { msg?: unknown }).msg;
        return typeof message === 'string' ? message : '';
      })
      .filter(Boolean);

    if (messages.length) return messages.join('; ');
  }

  return fallback;
}

/**
 * Utilitário de fetch resiliente a portas efêmeras bloqueadas/excluídas pelo Windows/Hyper-V (WSAEACCES / ERR_NETWORK_ACCESS_DENIED)
 */
async function fetchWithRetry(
  input: RequestInfo | URL,
  init?: RequestInit,
  maxAttempts = 4,
): Promise<Response> {
  let lastErr: unknown = null;
  const isGet = !init?.method || init.method.toUpperCase() === 'GET';
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      const res = await fetch(input, init);
      // Retenta requisições GET caso o proxy local devolva 5xx transitório
      if (isGet && res.status >= 500 && attempt < maxAttempts - 1) {
        await new Promise((resolve) => setTimeout(resolve, 100 * (attempt + 1)));
        continue;
      }
      return res;
    } catch (err) {
      lastErr = err;
      if (init?.signal?.aborted || (err as any)?.name === 'AbortError') {
        throw err;
      }
      await new Promise((resolve) => setTimeout(resolve, 80 * (attempt + 1)));
      if (init?.signal?.aborted) {
        throw err;
      }
    }
  }
  throw lastErr || new Error('Falha de rede ao conectar ao servidor.');
}

export const App: React.FC = () => {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [activeTab, setActiveTab] = useState<'auditoria' | 'rede'>('auditoria');
  const [documents, setDocuments] = useState<DocumentItem[]>([]);

  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const selectedDocIdRef = useRef<string | null>(selectedDocId);
  selectedDocIdRef.current = selectedDocId;

  const detailRequestVersion = useRef(0);

  const [docDetail, setDocDetail] = useState<DocumentDetail | null>(null);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);

  const [uploading, setUploading] = useState(false);
  const [loadingSeed, setLoadingSeed] = useState(false);
  const [submittingDecision, setSubmittingDecision] = useState(false);

  const [queueOpen, setQueueOpen] = useState(true);
  const [reviewOpen, setReviewOpen] = useState(true);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);

  const activeDetail =
    docDetail?.document.id === selectedDocId ? docDetail : null;

  // 1. Carrega configuração inicial do sistema
  useEffect(() => {
    fetchWithRetry('/api/config')
      .then((r) => (r.ok ? r.json() : null))
      .then((cfg: AppConfig | null) => {
        if (cfg) setConfig(cfg);
      })
      .catch((err) => console.error('Falha ao carregar config:', err));
  }, []);

  // 2. Carrega lista de documentos sem sobrescrever seleção ativa
  const refreshDocuments = async () => {
    try {
      const response = await fetchWithRetry('/api/documents');
      if (!response.ok) return;

      const docs: unknown = await response.json();
      if (!Array.isArray(docs)) return;

      setDocuments(docs as DocumentItem[]);
      if ((docs as DocumentItem[]).length > 0 && !selectedDocIdRef.current) {
        setSelectedDocId((docs as DocumentItem[])[0].id);
      }
    } catch (err) {
      console.error('Falha ao carregar documentos:', err);
    }
  };

  useEffect(() => {
    void refreshDocuments();
  }, []);

  // 3. Carrega detalhes do documento selecionado com cancelamento e proteção de corrida
  useEffect(() => {
    const requestVersion = ++detailRequestVersion.current;
    const controller = new AbortController();

    setDocDetail(null);
    setSelectedFinding(null);
    setDetailError(null);
    setReviewError(null);

    if (!selectedDocId) {
      setLoadingDetail(false);
      return () => controller.abort();
    }

    const requestedDocId = selectedDocId;
    setLoadingDetail(true);

    async function loadDetail() {
      try {
        const response = await fetchWithRetry(
          `/api/documents/${encodeURIComponent(requestedDocId)}`,
          { signal: controller.signal },
          5,
        );

        if (!response.ok) {
          throw new Error(`Falha ao carregar documento: HTTP ${response.status}`);
        }

        const detail: DocumentDetail = await response.json();

        if (controller.signal.aborted) return;
        if (requestVersion !== detailRequestVersion.current) return;
        if (selectedDocIdRef.current !== requestedDocId) return;

        if (detail.document.id !== requestedDocId) {
          throw new Error('A API retornou detalhes de outro documento.');
        }

        setDocDetail(detail);
        setSelectedFinding(detail.findings[0] ?? null);
      } catch (error) {
        if (controller.signal.aborted) return;
        if ((error as any)?.name === 'AbortError') return;
        if (requestVersion !== detailRequestVersion.current) return;
        if (selectedDocIdRef.current !== requestedDocId) return;

        setDetailError(
          error instanceof Error ? error.message : 'Erro ao carregar documento.',
        );
      } finally {
        if (
          !controller.signal.aborted &&
          requestVersion === detailRequestVersion.current &&
          selectedDocIdRef.current === requestedDocId
        ) {
          setLoadingDetail(false);
        }
      }
    }

    void loadDetail();

    return () => controller.abort();
  }, [selectedDocId]);

  // Seleção de documento com recuperação de erro caso o item já estivesse selecionado
  const handleSelectDoc = (id: string) => {
    if (selectedDocId === id && (detailError || !docDetail)) {
      setSelectedDocId(null);
      setTimeout(() => setSelectedDocId(id), 10);
    } else {
      setSelectedDocId(id);
    }
  };

  // Ação: Seed dos 20 casos sintéticos
  const handleSeedDemo = async () => {
    setLoadingSeed(true);
    try {
      const res = await fetchWithRetry('/api/admin/seed-demo', { method: 'POST' }, 4);
      if (res.ok) {
        await refreshDocuments();
      }
    } catch (err) {
      console.error('Falha ao preencher casos sintéticos:', err);
    } finally {
      setLoadingSeed(false);
    }
  };

  // Ação: Upload de nova imagem
  const handleUpload = async (file: File) => {
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetchWithRetry(
        '/api/documents',
        {
          method: 'POST',
          body: formData,
        },
        4,
      );

      if (res.ok) {
        const newDoc: DocumentItem = await res.json();
        await fetchWithRetry(
          `/api/documents/${newDoc.id}/runs`,
          { method: 'POST' },
          4,
        );
        await refreshDocuments();
        setSelectedDocId(newDoc.id);
      } else {
        const payload: unknown = await res.json().catch(() => null);
        alert(extractApiError(payload, 'Falha no upload do arquivo.'));
      }
    } catch (err) {
      alert(`Falha de rede ao enviar arquivo: ${String(err)}`);
    } finally {
      setUploading(false);
    }
  };

  // Ação: Enviar Decisão Humana com isolamento estrito
  const handleSubmitDecision = async (
    decisionData: ReviewSubmission,
  ): Promise<boolean> => {
    const targetDocId = selectedDocIdRef.current;

    if (!targetDocId || submittingDecision) return false;

    setSubmittingDecision(true);
    setReviewError(null);

    try {
      const response = await fetchWithRetry(
        `/api/documents/${encodeURIComponent(targetDocId)}/reviews`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...decisionData,
            actor_id: 'auditor-andre-01',
          }),
        },
        4,
      );

      if (!response.ok) {
        const payload: unknown = await response.json().catch(() => null);
        throw new Error(
          extractApiError(payload, `Revisão recusada: HTTP ${response.status}`),
        );
      }

      // A revisão já foi gravada no backend
      try {
        const detailResponse = await fetchWithRetry(
          `/api/documents/${encodeURIComponent(targetDocId)}`,
          undefined,
          4,
        );

        if (!detailResponse.ok) {
          throw new Error('Revisão salva, mas os detalhes não foram atualizados.');
        }

        const updatedDetail: DocumentDetail = await detailResponse.json();

        if (
          selectedDocIdRef.current === targetDocId &&
          updatedDetail.document.id === targetDocId
        ) {
          setDocDetail(updatedDetail);
          setSelectedFinding(updatedDetail.findings[0] ?? null);
        }
      } catch {
        if (selectedDocIdRef.current === targetDocId) {
          setReviewError(
            'Revisão salva. Não foi possível atualizar a tela; recarregue os detalhes.',
          );
        }
      }

      void refreshDocuments();
      return true;
    } catch (error) {
      if (selectedDocIdRef.current === targetDocId) {
        setReviewError(
          error instanceof Error ? error.message : 'Falha ao registrar revisão.',
        );
      }
      return false;
    } finally {
      setSubmittingDecision(false);
    }
  };

  const workspaceColumns = [
    queueOpen ? 'clamp(260px, 19vw, 340px)' : '0px',
    'minmax(0, 1fr)',
  ].join(' ');

  return (
    <div className="h-screen flex flex-col bg-slate-100 font-sans text-slate-800 overflow-hidden">
      <Header
        config={config}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onSeedDemo={handleSeedDemo}
        loadingSeed={loadingSeed}
        documents={documents}
      />

      {activeTab === 'auditoria' ? (
        <>
          {/* Barra de controle e estado dos painéis */}
          <div className="bg-white border-b border-slate-200 px-4 py-1.5 flex items-center justify-between text-xs text-slate-600 shrink-0">
            <div className="flex items-center gap-2">
              <button
                type="button"
                aria-expanded={queueOpen}
                aria-controls="document-queue"
                onClick={() => setQueueOpen((prev) => !prev)}
                className="px-2.5 py-1 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 rounded text-xs font-medium transition shadow-2xs flex items-center gap-1.5"
              >
                {queueOpen ? (
                  <>
                    <PanelLeftClose className="w-3.5 h-3.5 text-slate-500" />
                    <span>Ocultar fila</span>
                  </>
                ) : (
                  <>
                    <PanelLeftOpen className="w-3.5 h-3.5 text-slate-500" />
                    <span>Mostrar fila</span>
                  </>
                )}
              </button>

              <span className="text-slate-300">|</span>

              <span className="text-[11px] text-slate-500 font-medium">
                {activeDetail ? (
                  <span>
                    Documento ativo: <strong className="text-slate-800 font-mono">{activeDetail.document.id}</strong>
                  </span>
                ) : loadingDetail ? (
                  <span className="text-slate-500">Carregando documento...</span>
                ) : (
                  <span className="text-slate-400">Nenhum documento selecionado</span>
                )}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                aria-expanded={reviewOpen}
                aria-controls="review-panel"
                onClick={() => setReviewOpen((prev) => !prev)}
                className="px-2.5 py-1 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 rounded text-xs font-medium transition shadow-2xs flex items-center gap-1.5"
              >
                {reviewOpen ? (
                  <>
                    <PanelRightClose className="w-3.5 h-3.5 text-slate-500" />
                    <span>Ocultar revisão</span>
                  </>
                ) : (
                  <>
                    <PanelRightOpen className="w-3.5 h-3.5 text-slate-500" />
                    <span>Mostrar revisão</span>
                  </>
                )}
              </button>
            </div>
          </div>

          <main
            className="flex-1 min-h-0 grid overflow-hidden"
            style={{ gridTemplateColumns: workspaceColumns }}
          >
            {/* Fila de Documentos (Drawer recolhível sem perda de estado) */}
            <div
              className="h-full min-h-0 overflow-hidden flex flex-col"
              style={{ display: queueOpen ? 'flex' : 'none' }}
            >
              <DocumentQueue
                documents={documents}
                selectedDocId={selectedDocId}
                onSelectDoc={handleSelectDoc}
                onUpload={handleUpload}
                uploading={uploading}
              />
            </div>

            {/* Espaço de Trabalho do Documento: Visualizador + Painel de Revisão */}
            {activeDetail ? (
              <section
                data-testid="document-workspace"
                data-document-id={activeDetail.document.id}
                className="flex flex-1 min-w-0 min-h-0 h-full overflow-hidden"
                style={{
                  display: 'grid',
                  gridTemplateColumns: `minmax(0, 1fr) ${reviewOpen ? 'clamp(340px, 27vw, 460px)' : '0px'}`,
                }}
              >
                <DocumentViewer
                  documentId={activeDetail.document.id}
                  evidences={activeDetail.evidences}
                  selectedFinding={selectedFinding}
                  fields={activeDetail.fields}
                />

                <div
                  className="h-full min-h-0 overflow-hidden flex flex-col"
                  style={{ display: reviewOpen ? 'flex' : 'none' }}
                >
                  <FindingsPanel
                    key={activeDetail.document.id}
                    documentId={activeDetail.document.id}
                    fields={activeDetail.fields}
                    findings={activeDetail.findings}
                    decisions={activeDetail.decisions}
                    selectedFinding={selectedFinding}
                    onSelectFinding={setSelectedFinding}
                    onSubmitDecision={handleSubmitDecision}
                    submittingDecision={submittingDecision}
                    reviewError={reviewError}
                    onOpenReportModal={() => setIsReportModalOpen(true)}
                  />
                </div>
              </section>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500 font-sans text-sm p-6 bg-slate-50">
                {loadingDetail ? (
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-6 h-6 border-2 border-slate-400 border-t-slate-800 rounded-full animate-spin" />
                    <span className="text-slate-600 font-medium">Carregando detalhes do documento...</span>
                  </div>
                ) : detailError ? (
                  <div role="alert" className="max-w-md p-4 rounded bg-rose-50 border border-rose-200 text-rose-800 text-center shadow-xs">
                    <p className="font-semibold mb-1 text-sm">Falha no carregamento</p>
                    <p className="text-xs mb-3">{detailError}</p>
                    <button
                      type="button"
                      onClick={() => {
                        if (selectedDocId) {
                          const id = selectedDocId;
                          setSelectedDocId(null);
                          setTimeout(() => setSelectedDocId(id), 10);
                        }
                      }}
                      className="px-3 py-1 bg-white border border-rose-300 text-rose-700 hover:bg-rose-100 rounded text-xs font-medium"
                    >
                      Tentar novamente
                    </button>
                  </div>
                ) : (
                  <div className="text-center max-w-sm">
                    <p className="font-semibold text-slate-700 mb-1">Nenhum documento selecionado</p>
                    <p className="text-xs text-slate-500">
                      Selecione um caso na fila lateral ou clique em "Carregar 20 Casos Sintéticos" no cabeçalho.
                    </p>
                  </div>
                )}
              </div>
            )}
          </main>
        </>
      ) : (
        <main className="flex-1 flex overflow-hidden">
          <NetworkGraphView />
        </main>
      )}
      {activeDetail && (
        <ForensicReportModal
          isOpen={isReportModalOpen}
          onClose={() => setIsReportModalOpen(false)}
          document={activeDetail.document}
          imageUrl={`/api/documents/${encodeURIComponent(activeDetail.document.id)}/image`}
          fields={activeDetail.fields}
          evidences={activeDetail.evidences}
          findings={activeDetail.findings}
          decisions={activeDetail.decisions}
        />
      )}
    </div>
  );
};

export default App;
