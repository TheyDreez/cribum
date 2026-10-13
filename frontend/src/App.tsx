import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { DocumentQueue } from './components/DocumentQueue';
import { DocumentViewer } from './components/DocumentViewer';
import { FindingsPanel } from './components/FindingsPanel';
import { NetworkGraphView } from './components/NetworkGraphView';
import { AppConfig, DocumentDetail, DocumentItem, Finding } from './types';

export const App: React.FC = () => {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [activeTab, setActiveTab] = useState<'auditoria' | 'rede'>('auditoria');
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [docDetail, setDocDetail] = useState<DocumentDetail | null>(null);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [uploading, setUploading] = useState(false);
  const [loadingSeed, setLoadingSeed] = useState(false);
  const [submittingDecision, setSubmittingDecision] = useState(false);

  // 1. Carrega configuração inicial do sistema
  useEffect(() => {
    fetch('/api/config')
      .then((r) => r.json())
      .then((cfg: AppConfig) => setConfig(cfg))
      .catch((err) => console.error('Falha ao carregar config:', err));
  }, []);

  // 2. Carrega lista de documentos
  const refreshDocuments = () => {
    fetch('/api/documents')
      .then((r) => r.json())
      .then((docs: DocumentItem[]) => {
        setDocuments(docs);
        if (docs.length > 0 && !selectedDocId) {
          setSelectedDocId(docs[0].id);
        }
      })
      .catch((err) => console.error('Falha ao carregar documentos:', err));
  };

  useEffect(() => {
    refreshDocuments();
  }, []);

  // 3. Carrega detalhes do documento selecionado com proteção contra respostas atrasadas (race guard)
  useEffect(() => {
    if (!selectedDocId) {
      setDocDetail(null);
      return;
    }

    const abortController = new AbortController();
    let isCurrent = true;

    fetch(`/api/documents/${selectedDocId}`, { signal: abortController.signal })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP error ${r.status}`);
        return r.json();
      })
      .then((detail: DocumentDetail) => {
        if (!isCurrent) return;
        // Validação estrita: descarta resposta se pertencer a outro documento
        if (detail?.document?.id !== selectedDocId) return;

        setDocDetail(detail);
        if (detail.findings && detail.findings.length > 0) {
          setSelectedFinding(detail.findings[0]);
        } else {
          setSelectedFinding(null);
        }
      })
      .catch((err) => {
        if (err.name === 'AbortError') return;
        console.error('Falha ao carregar detalhe do documento:', err);
      });

    return () => {
      isCurrent = false;
      abortController.abort();
    };
  }, [selectedDocId]);

  // Ação: Seed dos 20 casos sintéticos
  const handleSeedDemo = async () => {
    setLoadingSeed(true);
    try {
      const res = await fetch('/api/admin/seed-demo', { method: 'POST' });
      if (res.ok) {
        refreshDocuments();
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
      const res = await fetch('/api/documents', {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        const newDoc: DocumentItem = await res.json();
        // Dispara processamento inicial
        await fetch(`/api/documents/${newDoc.id}/runs`, { method: 'POST' });
        refreshDocuments();
        setSelectedDocId(newDoc.id);
      } else {
        const err = await res.json();
        alert(`Erro no upload: ${err.detail || 'Arquivo rejeitado.'}`);
      }
    } catch (err) {
      alert(`Falha de rede ao enviar arquivo: ${String(err)}`);
    } finally {
      setUploading(false);
    }
  };

  // Ação: Enviar Decisão Humana
  const handleSubmitDecision = async (decisionData: {
    action: string;
    confirmed_value?: string;
    reason: string;
    finding_id?: string;
  }) => {
    if (!selectedDocId) return;

    setSubmittingDecision(true);
    try {
      const res = await fetch(`/api/documents/${selectedDocId}/reviews`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...decisionData,
          actor_id: 'auditor-andre-01',
        }),
      });

      if (res.ok) {
        // Recarrega detalhes e lista
        const detailRes = await fetch(`/api/documents/${selectedDocId}`);
        const updatedDetail: DocumentDetail = await detailRes.json();
        setDocDetail(updatedDetail);
        refreshDocuments();
      }
    } catch (err) {
      console.error('Falha ao submeter decisão humana:', err);
    } finally {
      setSubmittingDecision(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-graphite-950 font-sans">
      <Header
        config={config}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onSeedDemo={handleSeedDemo}
        loadingSeed={loadingSeed}
      />

      {activeTab === 'auditoria' ? (
        <main className="flex-1 flex overflow-hidden">
          {/* Fila de Documentos */}
          <DocumentQueue
            documents={documents}
            selectedDocId={selectedDocId}
            onSelectDoc={setSelectedDocId}
            onUpload={handleUpload}
            uploading={uploading}
          />

          {/* Área Central: Visualizador de Imagem com Bounding Boxes */}
          {selectedDocId && docDetail ? (
            <DocumentViewer
              documentId={selectedDocId}
              evidences={docDetail.evidences}
              selectedFinding={selectedFinding}
            />
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-500 font-mono text-xs">
              Selecione um documento na fila ou clique em "Carregar 20 Casos Sintéticos".
            </div>
          )}

          {/* Painel Lateral: Hipóteses, Alertas e Decisão Humana */}
          {docDetail && (
            <FindingsPanel
              documentId={selectedDocId!}
              fields={docDetail.fields}
              findings={docDetail.findings}
              decisions={docDetail.decisions}
              selectedFinding={selectedFinding}
              onSelectFinding={setSelectedFinding}
              onSubmitDecision={handleSubmitDecision}
              submittingDecision={submittingDecision}
            />
          )}
        </main>
      ) : (
        <main className="flex-1 flex overflow-hidden">
          <NetworkGraphView />
        </main>
      )}
    </div>
  );
};

export default App;
