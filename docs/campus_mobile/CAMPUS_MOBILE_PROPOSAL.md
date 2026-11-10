# CRIBUM MOBILE: PLATAFORMA DE SEGURANÇA FARMACÊUTICA INTELIGENTE, MULTIAGENTE E ASSISTIVA PARA O SUS
**Submissão Oficial: Campus Mobile (15ª Edição)**  
*Categoria: Saúde e Tecnologias Assistivas*  
*Realização: Instituto Claro | Escola Politécnica da USP (LSI-TEC) | BeOn Claro*  
*Autor e Titular dos Direitos de Propriedade Intelectual:* **André Rogério da Silva Filho**  
*Data de Atualização:* Novembro de 2026  

---

## 1. RESUMO EXECUTIVO E POSICIONAMENTO

O **CRIBUM Mobile** é uma plataforma de segurança farmacêutica inteligente que combina **arquitetura de IA multiagente**, **validação determinística**, **registro criptográfico offline-first** e **tecnologia assistiva** para resolver, em um único fluxo de ponta a ponta no celular, três problemas críticos do Sistema Único de Saúde (SUS) que historicamente são tratados de forma isolada:

1. **Segurança Clínica do Paciente:** prevenção ativa de erros de dispensação, divergências de concentração/dosagem (ex.: entregar Morfina 30 mg para uma receita de 10 mg) e trocas de medicamentos com grafia ou fonética semelhantes (*LASA: Look-Alike, Sound-Alike*, como Clorpromazina vs. Clomipramina);
2. **Integridade do Sistema Público (Antifraude):** rastreabilidade unitária por código bidimensional GS1 DataMatrix (padrão ANVISA RDC 157/2017 e RDC 319/2019) e prevenção/detecção de dispensações duplicadas em farmácias de alto custo (CEAF) e UBSs com conectividade instável;
3. **Inclusão e Acessibilidade Universal:** interface assistiva projetada para profissionais de saúde sob fadiga de plantão e pacientes idosos com baixa visão, daltonismo ou tremores motores.

Mais do que um aplicativo de saúde com IA, o CRIBUM Mobile adota um princípio central de engenharia de segurança médica: **a Inteligência Artificial atua exclusivamente como camada de assistência cognitiva e estruturação multimodal, enquanto a autoridade clínica de bloqueio permanece 100% em um Núcleo Determinístico auditável e imune a alucinações**.

---

## 2. O PROBLEMA TRIPLO NA PONTA DO SUS

### 2.1 Erros de Medicação, Trocas LASA e Divergência de Dosagem
Erros de medicação figuram entre as principais causas de danos evitáveis em saúde segundo a Organização Mundial da Saúde (*Medication Without Harm*). Na rotina de plantões sobrecarregados e no uso domiciliar por idosos com presbiopia, o cérebro humano recorre à leitura heurística e confunde embalagens quase idênticas:

| Medicamento Prescrito | Medicamento Trocado por Engano | Risco Clínico Direto |
| :--- | :--- | :--- |
| **Clorpromazina 25 mg** (Antipsicótico) | **Clomipramina 25 mg** (Antidepressivo tricíclico) | Síndrome neuroléptica maligna, arritmia grave e sedação severa |
| **Sulfato de Morfina 10 mg** (Analgésico opioide) | **Sulfato de Morfina 30 mg** (Mesmo fármaco, 3x a dose) | Depressão respiratória aguda e overdose acidental em idosos |
| **Doxorrubicina** (Oncológico) | **Daunorrubicina** (Oncológico) | Cardiotoxicidade severa por erro de equivalência posológica |
| **Hidralazina** (Anti-hipertensivo) | **Hidroxizina** (Anti-histamínico) | Hipotensão refratária ou falha de controle pressórico |

### 2.2 Desvios e Dispensações Duplicadas no Alto Custo (CEAF)
O Componente Especializado da Assistência Farmacêutica (CEAF) movimenta bilhões de reais anuais em medicamentos biológicos, imunossupressores e terapias raras (como Adalimumabe 40 mg, Trastuzumabe e Eculizumabe). Sem conferência criptográfica do número de série único (IUID) no ato da entrega e sem funcionamento offline confiável nas mais de 40.000 UBSs do país, o sistema fica vulnerável a:
- Registro duplicado da mesma embalagem física ("caixas fantasma");
- Desvio de lotes refrigerados de alto custo para o mercado paralelo;
- Entrega acidental de lotes vencidos por falha de conferência visual.

### 2.3 Exclusão Sensorial e Motora nas Interfaces de Saúde
Sistemas tradicionais de farmácia utilizam fontes reduzidas, botões pequenos e alertas baseados apenas no par verde/vermelho, excluindo pacientes idosos com tremor essencial ou baixa visão e profissionais com discromatopsia (daltonismo).

---

## 3. ARQUITETURA DE INTELIGÊNCIA ARTIFICIAL MULTIAGENTE E NÚCLEO DETERMINÍSTICO

Para atender aos critérios de complexidade técnica e inovação da 15ª Edição do Campus Mobile sem comprometer a segurança clínica nem a promessa *offline-first*, o CRIBUM Mobile implementa uma arquitetura híbrida dividida em **Orquestração Multiagente de Assistência** e **Núcleo Determinístico de Bloqueio**.

```
+---------------------------------------------------------------------------------------+
| 1. ENTRADA MULTIMODAL NA BORDA (SMARTPHONE / NAVEGADOR MOBILE)                        |
|    Receita Digital SUS (QR Code / OCR)  +  Câmera Óptica  +  GS1 DataMatrix (Caixa)   |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
| 2. ORQUESTRADOR MULTIAGENTE (CAMADA DE ASSISTÊNCIA COGNITIVA E ESTRUTURAÇÃO)          |
|                                                                                       |
|  +---------------------------------------+  +--------------------------------------+  |
|  | Agente de Leitura [100% On-Device]    |  | Agente de Conciliação [On-Device]    |  |
|  | Extrai princípio ativo, concentração  |  | Normaliza nomenclatura DCB/ANVISA,   |  |
|  | em mg/mL, posologia e AIs GS1 (01,    |  | converte unidades (1g = 1000mg) e    |  |
|  | 17, 10, 21) mesmo sob ruído óptico.   |  | cruza prescrição vs. item físico.    |  |
|  +---------------------------------------+  +--------------------------------------+  |
|                                                                                       |
|  +---------------------------------------+  +--------------------------------------+  |
|  | Agente de Segurança LASA [On-Device]  |  | Agente de Auditoria [Híbrido 5G]     |  |
|  | Calcula similaridade fonética PT-BR e |  | Verifica manifesto local da UBS,     |  |
|  | Levenshtein, aplica Tall Man Lettering|  | sincroniza com pares na LAN e        |  |
|  | e sintetiza alerta vocal acessível.   |  | reconcilia raízes na borda 5G SA / MEC. |  |
|  +---------------------------------------+  +--------------------------------------+  |
+-------------------------------------------+-------------------------------------------+
                                            | Resposta Estruturada Padronizada (JSON)
                                            v
+---------------------------------------------------------------------------------------+
| 3. NÚCLEO DETERMINÍSTICO CRIBUM (AUTORIDADE CLÍNICA INVIOLÁVEL - ON-DEVICE)           |
|    - Trava matemática de divergência de concentração (ex.: 30 mg != 10 mg -> BLOQUEIO)|
|    - Validação de dígito verificador GTIN Módulo 10 e vigência de validade GS1        |
|    - Registro Append-Only em Árvore de Merkle (RFC 6962) + Hash LGPD HMAC-SHA256      |
|    * Regra de Ouro: A IA auxilia e explica, mas NUNCA autoriza dispensação sozinha.   |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
| 4. DECISÃO ASSISTIDA PELO PROFISSIONAL / PACIENTE                                     |
|    Homologação segura, alerta com dupla confirmação humana ou bloqueio imediato.      |
+---------------------------------------------------------------------------------------+
```

### 3.1 Responsabilidades dos Agentes e Separação Online vs. Offline

Para que a operação *offline-first* seja tecnicamente íntegra, o CRIBUM Mobile define de forma estrita onde cada agente opera:

| Componente / Agente | Função no Fluxo de Trabalho | Execução no Dispositivo (Offline) | Execução Conectada (5G SA / Nuvem) | Autoridade Clínica |
| :--- | :--- | :--- | :--- | :--- |
| **Agente de Leitura** | Interpretação da prescrição (QR Code SUS / texto) e extração dos campos GS1 DataMatrix da embalagem. | **100% On-Device** (WebAssembly / câmera local). | Atualização periódica de modelos ópticos leves. | Nenhuma (apenas extração). |
| **Agente de Conciliação** | Normalização para Denominação Comum Brasileira (DCB) e equivalência de unidades (`g`, `mg`, `mcg`, `UI/mL`). | **100% On-Device** sobre dicionário ANVISA compactado em IndexedDB. | Sincronização de novos registros regulatórios da ANVISA. | Nenhuma (apenas mapeamento). |
| **Agente de Segurança LASA** | Detecção de pares fonéticos/ortográficos de alto risco, formatação *Tall Man Lettering* e adaptação para linguagem simples e voz. | **100% On-Device** (motor fonético PT-BR + Web Speech API nativa). | Telemetria agregada e anônima de quase-erros (*near misses*). | Consultiva (dispara alerta obrigatório). |
| **Agente de Auditoria** | Detecção de seriais repetidos, validação de lote alocado à UBS e correlação de anomalias entre unidades. | **Local + LAN P2P** (verifica árvore de Merkle local e pares na mesma UBS). | **Reconciliação Federada 5G SA** (cruzamento inter-UBSs em MEC). | Consultiva e forense. |
| **Núcleo Determinístico CRIBUM** | Execução das travas formais de dosagem, validade, integridade GS1 e selagem criptográfica na Árvore de Merkle. | **100% On-Device** (código determinístico auditável). | Publicação de raízes assinadas (`Merkle Root`). | **Autoridade Final de Bloqueio.** |

---

## 4. ENGENHARIA ANTIFRAUDE: COMO O CRIBUM RESOLVE O PROBLEMA DE DOIS CELULARES DESCONECTADOS

Uma questão técnica fundamental em sistemas distribuídos é: *uma Árvore de Merkle local garante a integridade do histórico naquele aparelho e impede que o mesmo celular dispense duas vezes a mesma caixa, mas como impedir ou detectar que dois celulares desconectados dispensem a mesma unidade física (ou uma caixa clonada)?*

O CRIBUM Mobile resolve esse desafio clássico do Teorema CAP (*Consistency, Availability, Partition Tolerance*) por meio de uma **Arquitetura de Defesa em Três Camadas**:

1. **Camada 1 (Prevenção Offline por Manifesto de Lote Alocado à UBS):**  
   Na cadeia do CEAF/Hórus, lotes e faixas de seriais (`GTIN + Lote + Filtro de Bloom de Seriais`) são alocados especificamente para o CNES de cada farmácia pública. O manifesto assinado dos lotes destinados àquela UBS é carregado no dispositivo no início do expediente. Se um serial pertencente ao lote da UBS "A" for escaneado offline na UBS "B", o Núcleo Determinístico barra a entrega imediatamente por **Incompatibilidade de Alocação Territorial**, mesmo sem internet.
2. **Camada 2 (Prevenção Intra-Unidade via Sincronização Local P2P na mesma Farmácia):**  
   Dentro de uma mesma farmácia pública com múltiplos balconistas mas sem internet externa, os dispositivos trocam novas folhas da Árvore de Merkle via rede local (Wi-Fi local / WebRTC LAN Gossip). Assim, se uma caixa acabar de ser dispensada no Guichê 1, o Guichê 2 da mesma unidade recebe o hash do serial em sub-segundo, sem depender de servidor na nuvem.
3. **Camada 3 (Reconciliação Compartilhada e Prova Forense de Colisão entre Unidades via Redes 5G SA):**  
   Caso uma embalagem clonada do mesmo lote seja apresentada simultaneamente em dois dispositivos totalmente isolados sem comunicação local, o sistema prioriza a disponibilidade assistencial com registro assinado e executa a **Detecção Forense Inevitável na Reconciliação**: assim que qualquer dispositivo recupera sinal 5G/4G, sua Raiz de Merkle e folhas pendentes são sincronizadas com o nó regional (nó MEC). A colisão do identificador `SHA256(GTIN + Serial)` entre duas árvores gera automaticamente uma **Prova Criptográfica de Colisão (`Serial Collision Proof`)** contendo o carimbo de tempo, o CNES e a assinatura dos dois pontos, bloqueando instantaneamente o lote residual e acionando auditoria.

---

## 5. DISTINÇÃO ENTRE RESULTADOS COMPROVADOS NO PROTÓTIPO E METAS DE VALIDAÇÃO EM CAMPO

Para assegurar rigor científico e transparência perante a banca avaliadora, os indicadores técnicos do CRIBUM Mobile são divididos entre o que **já está implementado e medido no protótipo funcional** e o que constitui **meta de arquitetura (SLA) para validação em campo**:

| Indicador Técnico | Status no Protótipo Atual (Comprovado em Bancada) | Meta de Arquitetura / Validação em Campo (SLA) |
| :--- | :--- | :--- |
| **Bloqueio de Divergência de Dose e LASA** | **100% funcional no motor determinístico** sobre os cenários clínicos de teste (ex.: Morfina 30 mg vs. 10 mg; Clorpromazina vs. Clomipramina). | Validação prospectiva com farmacêuticos do SUS sobre catálogo expandido da RENAME. |
| **Detecção de Duplicidade Local (Merkle RFC 6962)** | **100% funcional em código** (`cribum_core.py` e `simulator.html`), com separação de domínio `0x00`/`0x01` e geração de *Audit Proofs*. | Teste de estresse de sincronização multi-nó entre múltiplas UBSs em ambiente real. |
| **Acessibilidade Visual e Contraste (Okabe-Ito)** | **Implementado:** paleta segura para daltonismo com razão de contraste medida de **9,4:1** nos cartões de decisão (acima do limiar 7:1 exigido pela WCAG 2.2 AAA para texto normal). | Auditoria completa de conformidade WCAG 2.2 AAA com usuários com baixa visão e daltonismo. |
| **Tempo de Conferência no Balcão** | Execução algorítmica local inferior a 50 ms após captura do código. | **Meta de SLA operacional:** concluir o ciclo completo de leitura óptica + confirmação humana em **menos de 3 segundos**. |
| **Filtro Motor Anti-Tremor (Debounce/Histerese)** | **Implementado:** filtro temporal de 350 ms e alvos de toque de 60x60dp na interface mobile. | **Meta de validação assistiva:** reduzir em **mais de 90%** os toques involuntários em testes com idosos com tremor essencial ou Parkinson. |
| **Reconciliação de Raízes em Borda 5G** | Simulação de payload criptográfico enxuto (32 bytes por raiz de Merkle). | **Meta de arquitetura em redes 5G SA + MEC:** latência de sincronização de borda **inferior a 10 ms**. |

---

## 6. ESTRATÉGIA DE VALIDAÇÃO COM USUÁRIOS REAIS E VIABILIDADE DE ADOÇÃO NO SUS

O maior desafio de soluções para saúde pública não é apenas tecnológico, mas demonstrar viabilidade operacional no cotidiano do SUS. Nossa estratégia de validação e adoção está estruturada em três pilares práticos:

### 6.1 Protocolo de Validação com Profissionais de Saúde e Pacientes Idosos
Durante o ciclo da 15ª Edição do Campus Mobile, a validação empírica seguirá três etapas objetivas:
1. **Entrevistas Estruturadas e Teste de Bancada com Farmacêuticos e Técnicos de Enfermagem (UBS / Farmácia de Alto Custo):**  
   Simulação controlada de plantão utilizando caixas reais com etiquetas GS1 DataMatrix e pares LASA críticos, medindo a redução de erros induzidos por fadiga, o tempo de conferência e a carga mental percebida (protocolo **NASA-TLX**).
2. **Ensaio de Usabilidade Assistiva com Pacientes Idosos (65+ anos) e Cuidadores:**  
   Avaliação da compreensão dos alertas em linguagem simples, eficácia da leitura em voz alta e precisão de toque com o filtro anti-tremor ativado, utilizando a escala padronizada **System Usability Scale (SUS Score, meta > 80 pontos)**.
3. **Articulação Institucional para Piloto:**  
   Busca de carta de interesse para teste piloto não-intervencionista junto a farmácias-escola universitárias (como a Farmácia Universitária da USP / unidades ligadas ao ecossistema acadêmico) e secretarias municipais de saúde.

### 6.2 Estratégia de Adoção Progressiva no SUS (Sem Substituir Sistemas Legados)
O CRIBUM Mobile não exige que o Ministério da Saúde ou as prefeituras desativem o **Hórus** ou o **e-SUS APS**:
- **Fase 1 (Utilitário Assistivo Standalone Zero-Instalação):** Funciona imediatamente como *Progressive Web App (PWA)* em qualquer smartphone de paciente, cuidador ou profissional de saúde para conferência visual/vocal da receita contra a caixa, exigindo **custo zero de integração de TI**.
- **Fase 2 (Camada Complementar de Auditoria em Farmácias Municipais/CEAF):** Opera como leitor óptico de bolso conectado via exportação padrão JSON/FHIR ao controle de estoque da unidade.
- **Fase 3 (Sinergia B2Gov de Conectividade):** Oferta como solução de valor agregado sobre planos corporativos móveis e infraestrutura de redes 5G Standalone para Secretarias Estaduais e Municipais de Saúde.

---

## 7. ROTEIRO DO VÍDEO PITCH COMERCIAL (VERSÃO ATUALIZADA COM ARQUITETURA MULTIAGENTE: ~85 SEGUNDOS)

*Dentro do limite oficial de até 2 minutos (120 segundos) do regulamento da 15ª Edição.*

- **`00:00 - 00:04` (Cena 1: Fadiga no Plantão e Risco LASA):**  
  *"Um segundo de exaustão no plantão basta para confundir dois nomes quase idênticos na prateleira."*
- **`00:04 - 00:13` (Cena 2: Paciente Idosa e Dose Divergente):**  
  *"Em casa, para quem tem mais de setenta anos e baixa visão, uma caixa de Morfina de trinta miligramas parece igual à de dez miligramas da receita, mas carrega três vezes a dose prescrita."*
- **`00:13 - 00:22` (Cena 3: Desvios no Alto Custo e Operação Offline):**  
  *"Enquanto erros de medicação causam milhares de internações evitáveis, fraudes e desvios em unidades sem internet confiável drenam bilhões de reais da saúde no Brasil todos os anos."*
- **`00:22 - 00:35` (Cena 3B: Arquitetura Multiagente + Núcleo Determinístico CRIBUM):**  
  *"Para proteger as duas pontas, nasce o CRIBUM Mobile: uma arquitetura multiagente no dispositivo para leitura, conciliação e segurança LASA, aliada a um núcleo determinístico inviolável que nunca delega o bloqueio clínico à inteligência artificial."*
- **`00:35 - 01:13` (Cena 4: Demonstração Real do Sistema Mobile em 5 Cenários):**  
  *"Direto no navegador do celular e cem por cento offline, o sistema lê a Receita Digital do SUS e confere o código GS1 DataMatrix da caixa. Se a concentração for divergente, o sistema bloqueia o uso na hora e alerta em voz alta: dose três vezes mais forte que a receita. Se os nomes forem parecidos, o padrão internacional Tall Man Lettering destaca as letras críticas para impedir a troca entre um antipsicótico e um antidepressivo. Quando a caixa está correta, a entrega é homologada e selada localmente em uma árvore de Merkle criptográfica. Se a mesma embalagem de alto custo for escaneada uma segunda vez, o CRIBUM intercepta a duplicidade sem depender de servidor central. Com um toque, a interface alterna entre a linguagem simples para o paciente, a visão forense para o farmacêutico do SUS e o modo de alto contraste Okabe-Ito com filtro anti-tremor."*
- **`01:13 - 01:25` (Cena 5 e Cena 6: Reconciliação Compartilhada 5G Standalone + End Card):**  
  *"E quando há cobertura 5G Standalone, as árvores locais são reconciliadas em um registro compartilhado entre unidades, fechando o cerco contra desvios. CRIBUM Mobile. Segurança clínica e antifraude. Na palma da mão."*

---

*CRIBUM Mobile. Propriedade Intelectual estritamente pessoal de André Rogério da Silva Filho. Desenvolvido para a 15ª Edição do Campus Mobile.*
