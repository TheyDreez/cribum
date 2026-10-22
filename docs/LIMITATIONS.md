# Limitações Conhecidas e Escopo do Sistema (CRIBUM)

Para garantir máxima transparência técnica, científica e regulatória perante avaliadores e auditores do **Campus Mobile, do Instituto Claro**, este documento descreve o escopo formal do protótipo **CRIBUM (AuditRx)**, bem como suas limitações operacionais conhecidas.

---

## 1. Aviso Regulatório — Não é Dispositivo Médico (SaMD)
* O **CRIBUM** é um protótipo experimental de engenharia de software voltado à auditoria documental, segurança de processos e apoio à conferência de prescrições.
* **Não possui registro na ANVISA como Software as a Medical Device (SaMD)** e **não substitui** o julgamento clínico privativo de médicos, farmacêuticos, enfermeiros ou auditores de saúde.
* O sistema opera estritamente sob o paradigma **Human-in-the-Loop (HITL)** obrigatório: nenhuma decisão de dispensação ou glosa é tomada de forma autônoma pelo software sem validação e assinatura de um profissional responsável.

---

## 2. Modos de Leitura: Deterministic Fixture Engine vs. VLM Live
* **Modo Padrão (Offline / Demonstração):** Opera com o `Deterministic Fixture Engine`, que carrega extrações estruturadas e auditadas correspondentes aos 20 casos do catálogo sintético (`backend/data/synthetic/`). Isso assegura **100% de reprodutibilidade científica** para avaliadores, sem custos de API externa, sem latência imprevisível e sem dependência de GPU física local.
* **Modo VLM Live (Produção / GPU On-Premise):** Projetado para conectar-se a servidores locais de inferência multimodal (`vLLM` com `Qwen2-VL-7B-Instruct`) ou endpoints compatíveis. A acurácia em receitas médicas manuscritas reais varia conforme a qualidade da digitalização, iluminação e estilo caligráfico.

---

## 3. Escopo da Base Clínica e Pares LASA
* A verificação de medicamentos com grafia ou som semelhantes (*Look-Alike, Sound-Alike* — **LASA**) neste repositório utiliza um recorte referencial de **10 pares críticos** fundamentados nas publicações técnicas do **ISMP Brasil (Instituto para Práticas Seguras no Uso de Medicamentos)** (`backend/data/references/lasa_ismp.json`).
* **Não cobre a totalidade do bulário nacional**, CMED ou RENAME da ANVISA nesta versão de protótipo.
* Alertas de posologia e unidades baseiam-se em checagens determinísticas de presença de dados; ajustes farmacocinéticos complexos (peso, clearance renal, superfície corporal) não fazem parte do escopo atual.

---

## 4. Dados Sintéticos e Métricas de Avaliação (`eval/run_eval.py`)
* Todas as prescrições médicas em imagem (`.jpg`), matrizes de gabarito (*ground truth* `.json`) e a rede de 200 sinistros (`claims_200.json`) são **100% sintéticas**, geradas programaticamente e livres de dados de pacientes reais (em estrita observância à **LGPD**).
* O script de avaliação (`eval/run_eval.py`) afere a **consistência determinística interna entre as fixtures gabaritadas e o motor de regras/grafos**. O resultado de 100% obtido no script mede a consistência do pipeline lógico sobre os casos de referência catalogados, e **não deve ser interpretado como taxa de acerto de OCR em caligrafia livre de prontuários hospitalares reais**.

---

## 5. Ausência de Integração Externa em Tempo Real (CFM / CNES / ANS)
* A validação de CRM verifica a presença e formatação estrutural do registro (dígitos e UF), além de cruzamentos topológicos na rede local de sinistros. Não realiza consultas ativas em tempo real às bases remotas do Conselho Federal de Medicina (CFM), CNES ou barramentos TISS das operadoras.
* Anomalias geográficas no grafo (ex.: faturamentos simultâneos em municípios distantes) constituem **indícios documentais para triagem**, exigindo conferência humana (podem decorrer de telemedicina legítima ou escala de plantão).

---

## 6. Aceleração de Hardware (AMD ROCm / vLLM)
* O repositório inclui a configuração containerizada de produção (`docker/docker-compose.rocm.yml`) e documentação técnica de implantação (`docs/AMD_SETUP.md`) prontas para aceleradores AMD Instinct / ROCm 6.2.
* A execução padrão de testes de unidade e CI/CD é realizada em CPU comum para portabilidade em qualquer estação de trabalho de avaliadores.
