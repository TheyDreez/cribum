# LIMITAÇÕES TÉCNICAS, CLÍNICAS E OPERACIONAIS CONHECIDAS

Em conformidade com a ética de engenharia e as regras de segurança da **Trilha Health and Wellbeing**, este documento lista as limitações explícitas do MVP do CRIBUM / AuditRx.

---

## 1. Limitações Clínicas e Terapêuticas

1. **Não é Dispositivo Médico nem Sistema de Diagnóstico:** O CRIBUM é estritamente uma ferramenta de apoio à conferência documental para auditores administrativos. Não diagnostica pacientes, não prescreve tratamentos e não substitui o juízo clínico de médicos ou farmacêuticos.
2. **Cobertura Farmacêutica Parcial:** A base de referência de pares LASA implementada contém 10 pares críticos do ISMP Brasil com propósito didático e de validação. Não cobre o universo integral de especialidades farmacêuticas registradas na Anvisa.
3. **Contexto de Posologia:** O sistema alerta para dosagens incomuns ou unidades ausentes com base em regras heurísticas básicas. Ajustes de dose por peso pediátrico ou função renal/hepática não são calculados.

---

## 2. Limitações de Visão Computacional e Modelos de Linguagem

1. **Probabilidades Não Calibradas:** Os scores percentuais atribuídos às hipóteses pelo VLM (Vision-Language Model) representam estimativas heurísticas do modelo e **não devem ser interpretados como probabilidades estatísticas matematicamente calibradas**.
2. **Localização Visual Aproximada:** Bounding boxes extraídos por modelos de visão aberta podem sofrer deslocamentos marginais ou cobrir trechos ligeiramente adjacentes do texto. Por isso, a interface sempre mantém a visualização do documento completo acessível.
3. **Caligrafia Real vs. Sintética:** Os testes foram executados com formulários sintéticos e simulações. A eficácia em receitas manuais reais em papel vegetal ou carbono degradado exigirá fine-tuning específico.

---

## 3. Limitações de Análise de Rede e Fraude

1. **Indício vs. Prova:** Um alerta de "atendimento em cidades distantes no mesmo dia" indica uma inconsistência de agenda documental, mas **não constitui prova jurídica de fraude**. Pode decorrer de erro de digitação de data no faturamento ou atendimento legítimo via telemedicina.
2. **Ausência de Dados Cadastrais Externos:** O MVP opera com dados sintéticos isolados sem integração aos bancos de dados oficiais do CFM/CRM, CNES (Cadastro Nacional de Estabelecimentos de Saúde) ou Receita Federal.
