# ROTEIRO DE DEMONSTRAÇÃO DO PITCH (3 MINUTOS)

**Hackathon:** AMD Developer Hackathon: ACT III  
**Equipe:** Inédito Viável  
**Produto:** CRIBUM / AuditRx  

---

### [0:00 – 0:40] CENA 1: A Dor Real e a Admissão de Incerteza
* **Narrativa do Apresentador:**
  > *"Todo ano, bilhões de reais são perdidos em fraudes e erros de dispensação causados por receitas ambíguas. O erro clássico de OCRs convencionais é tentar adivinhar com 100% de falsa certeza palavras ilegíveis. O CRIBUM adota outra premissa: uma IA que admite dúvida e ancora cada suspeita em evidências visuais."*
* **Ação na Tela:**
  * O apresentador abre o navegador no CRIBUM (`http://localhost:5173`).
  * Mostra o banner superior: `MODO DEMO ATIVO: Resultados originados de fixtures documentadas`.
  * Clica no documento `caso_01_losartana_lorazepam.jpg`.
  * Mostra que o modelo não cravou apenas um remédio: gerou **Hipótese 1 (Losartana 50mg)** e **Hipótese 2 (Lorazepam 2mg)**, com badge em âmbar: `Ambiguidade Detectada`.

---

### [0:40 – 1:25] CENA 2: Rastreabilidade Visual e Decisão Humana (*HITL*)
* **Narrativa do Apresentador:**
  > *"O CRIBUM detectou um risco crítico de troca LASA (ISMP Brasil): um anti-hipertensivo vs. um ansiolítico potente. Ao clicar no alerta 'Ver Evidência', a caixa delimitadora SVG ilumina o traçado exato na receita. O auditor humano analisa o CID-10 de hipertensão (I10), clica em 'Confirmar Losartana', escreve a fundamentação e registra a decisão. A IA apoia, mas a decisão final é humana e auditável."*
* **Ação na Tela:**
  * Clica em "Ver Evidência" no painel de alertas; o retângulo vermelho se acende na imagem.
  * Seleciona o radio button de *Losartana 50mg*.
  * Preenche o parecer e clica em *Registrar Decisão no Prontuário*.
  * Mostra a decisão sendo salva no histórico persistido do SQLite.

---

### [1:25 – 2:15] CENA 3: Rede de Guias (Grafo de Anomalias com NetworkX)
* **Narrativa do Apresentador:**
  > *"Mas a auditoria moderna vai além de uma folha isolada. Na aba 'Rede de Guias', o CRIBUM modela 200 guias sintetizadas em um grafo multientidade conectando pacientes, médicos, clínicas e procedimentos via NetworkX."*
* **Ação na Tela:**
  * Alterna para a aba *Rede de Guias (Grafo)*.
  * O painel exibe a topologia e destaca a anomalia: `Atendimento Simultâneo em Cidades Distintas (CRM PROF-DEMO-007)`.
  * Mostra as clínicas em Sorocaba e Santos (180 km) faturadas no mesmo dia pelo mesmo profissional.
  * Destaca o texto de limitação: *"Apresentado como indício para revisão, não como acusação automática."*

---

### [2:15 – 3:00] CENA 4: Infraestrutura AMD ROCm & Conclusão
* **Narrativa do Apresentador:**
  > *"Por trás dessa inteligência, temos modelos visuais abertos projetados para rodar localmente no stack AMD ROCm via vLLM. Zero dados de pacientes saem para APIs comerciais proprietárias. Nossa arquitetura separa estritamente o modo DEMO do modo REAL — sem mocks silenciosos. Construímos uma ferramenta que traz transparência, evidência e soberania de dados para a auditoria de saúde."*
* **Ação na Tela:**
  * Mostra a tela de configuração `/api/config` e o terminal com o container vLLM ROCm.
  * Encerra com a logo da equipe Inédito Viável e o repositório GitHub.
