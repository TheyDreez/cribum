from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

class ItemHypothesis(BaseModel):
    """Uma das 3 hipóteses de leitura geradas pelo Leitor VLM."""
    nome: str = Field(..., description="Nome do medicamento ou procedimento lido")
    confianca: float = Field(..., ge=0.0, le=1.0, description="Nível de confiança probabilística (0.0 a 1.0)")

class PrescriptionItem(BaseModel):
    """Item individual da receita ou procedimento com ancoragem visual."""
    id: str = Field(..., description="Identificador único do item na guia (ex: item_1)")
    box: List[int] = Field(..., min_length=4, max_length=4, description="Bounding box [ymin, xmin, ymax, xmax] normalizado 0-1000")
    hipoteses: List[ItemHypothesis] = Field(..., min_length=1, max_length=3, description="Até 3 hipóteses de leitura ordenadas por probabilidade")
    posologia: Optional[str] = Field(None, description="Dose, via de administração e frequência extraída")
    nivel_incerteza: Literal["baixo", "medio", "alto"] = Field(..., description="Grau de dúvida na leitura visual")
    justificativa_leitura: str = Field(..., description="Explicação do modelo sobre caligrafia, ambiguidades e contexto")

class HeaderData(BaseModel):
    """Metadados e cabeçalho extraídos da guia médica."""
    crm: Optional[str] = Field(None, description="Número do CRM do médico prescritor")
    uf_crm: Optional[str] = Field(None, description="Estado do CRM (ex: SP)")
    data_emissao: Optional[str] = Field(None, description="Data da emissão no formato YYYY-MM-DD")
    paciente_nome: Optional[str] = Field(None, description="Nome do paciente")
    paciente_cpf: Optional[str] = Field(None, description="CPF do paciente (se presente)")
    clinica_nome: Optional[str] = Field(None, description="Nome da clínica ou hospital emissor")
    clinica_cnpj: Optional[str] = Field(None, description="CNPJ da clínica")
    diagnostico_cid: Optional[str] = Field(None, description="Código CID-10 indicado na guia")
    boxes: Optional[Dict[str, List[int]]] = Field(default_factory=dict, description="Bounding boxes dos campos do cabeçalho")

class PharmacistAlert(BaseModel):
    """Alerta gerado pelo agente Farmacêutico sobre segurança e compatibilidade."""
    item_id: str = Field(..., description="ID do item correspondente")
    tipo: Literal[
        "LASA_CONFLITO",
        "DOSE_INCOMPATIVEL",
        "INTERACAO_MEDICAMENTOSA",
        "DIAGNOSTICO_INCOMPATIVEL"
    ] = Field(..., description="Tipo do alerta farmacêutico")
    gravidade: Literal["BAIXA", "MEDIA", "ALTA", "CRITICA"] = Field(..., description="Severidade clínica do risco")
    droga_suspeita: str = Field(..., description="Droga prescrita/lida")
    droga_conflito: Optional[str] = Field(None, description="Droga alternativa de confusão LASA")
    mensagem: str = Field(..., description="Detalhamento clínico do risco e recomendação para o auditor")
    box: Optional[List[int]] = Field(None, description="Bounding box na imagem para destacar na interface")

class NetworkAnomaly(BaseModel):
    """Anomalia identificada pelo agente Investigador no grafo paciente-médico-clínica."""
    tipo_anomalia: Literal[
        "CRM_DISTANCIA_IMPOSSIVEL",
        "GUIAS_SIMULTANEAS",
        "VOLUME_DISCREPANTE",
        "CLINICA_FANTASMA",
        "RECIPROCIDADE_SUSPEITA"
    ] = Field(..., description="Padrão de fraude ou anomalia sistêmica detectado")
    score_anomalia: float = Field(..., ge=0.0, le=100.0, description="Pontuação de risco da anomalia (0 a 100)")
    descricao: str = Field(..., description="Explicação contextual da evidência em rede")
    guias_relacionadas: List[str] = Field(default_factory=list, description="IDs das outras guias que formam o esquema")
    evidencias: Dict[str, Any] = Field(default_factory=dict, description="Dados brutos que comprovam a anomalia (ex: distância, horários)")

class HumanDecision(BaseModel):
    """Registro da supervisão humana (Human-in-the-Loop) obrigatória para fechamento da guia."""
    status: Literal[
        "PENDENTE",
        "APROVADO",
        "REJEITADO_FRAUDE",
        "REJEITADO_ERRO_CLINICO",
        "SOLICITADO_ESCLARECIMENTO"
    ] = Field(default="PENDENTE", description="Decisão final do auditor humano")
    auditor_id: Optional[str] = Field(None, description="Identificação do auditor responsável")
    data_revisao: Optional[str] = Field(None, description="Timestamp ISO da decisão humana")
    hipotese_selecionada_por_item: Dict[str, int] = Field(
        default_factory=dict,
        description="Mapeamento item_id -> índice da hipótese confirmada pelo auditor (0, 1 ou 2)"
    )
    observacao_humana: Optional[str] = Field(None, description="Parecer justificado do auditor")

class AuditDossier(BaseModel):
    """Dossiê completo de auditoria da guia (integrando todos os agentes e a cadeia de custódia)."""
    documento_id: str = Field(..., description="ID único da guia auditada")
    documento_sha256: str = Field(..., description="Hash criptográfico SHA-256 do arquivo original para verificação de integridade documental")
    image_path: str = Field(..., description="Caminho relativo ou absoluto da imagem original")
    timestamp_auditoria: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Timestamp ISO da auditoria")
    score_risco_global: float = Field(..., ge=0.0, le=100.0, description="Risco consolidado (0 = seguro, 100 = fraude/erro crítico)")
    status_geral: Literal["SEGURO", "ALERTA_CLINICO", "SUSPEITA_FRAUDE", "BLOQUEADO"] = Field(..., description="Classificação do dossiê")
    cabecalho: HeaderData
    itens: List[PrescriptionItem] = Field(default_factory=list)
    alertas_farmaceuticos: List[PharmacistAlert] = Field(default_factory=list)
    anomalias_rede: List[NetworkAnomaly] = Field(default_factory=list)
    decisao_humana: HumanDecision = Field(default_factory=HumanDecision)
    telemetria_gpu: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Métricas da GPU AMD: tempo de inferência (ms), VRAM alocada (MB), modelo utilizado"
    )
