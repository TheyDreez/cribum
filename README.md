# CRIBUM Mobile: Segurança Farmacêutica Inteligente e Acessível

<div align="center">

<img src="docs/assets/cribum_binary_shield.gif" alt="CRIBUM: escudo formado por bits, com varredura de auditoria" width="280">

### *Plataforma de Segurança Farmacêutica Multiagente, Offline-First e Criptográfica*
**Projeto submetido à 15ª Edição do Campus Mobile (Instituto Claro / Escola Politécnica da USP / BeOn Claro)**  
*Categoria: Saúde e Tecnologias Assistivas*

[![Campus Mobile](https://img.shields.io/badge/Campus%20Mobile-15%C2%AA%20Edi%C3%A7%C3%A3o-blue)](https://www.institutoclaro.org.br/campus-mobile/)
[![Python Tests](https://img.shields.io/badge/Python%20Core-100%25%20Passing-success)](cribum_core.py)
[![RFC 6962](https://img.shields.io/badge/Merkle%20Tree-RFC%206962%20Compliant-10b981)](https://datatracker.ietf.org/doc/html/rfc6962)
[![GS1 Standard](https://img.shields.io/badge/GS1-DataMatrix%20ANVISA%20RDC%20319-orange)](https://www.gov.br/anvisa/)
[![A11y](https://img.shields.io/badge/Accessibility-Okabe--Ito%20AAA%20(9.4:1)-purple)](simulator.html)
[![License](https://img.shields.io/badge/License-Source--Available%20Evaluation-green.svg)](LICENSE)

</div>

---

## 🎬 Vídeo Oficial de Demonstração (Campus Mobile)

Assista ao vídeo pitch de demonstração (84 segundos) apresentando a arquitetura multiagente, o motor determinístico e o simulador mobile em funcionamento:

👉 **[▶️ Assistir no YouTube: https://youtu.be/e7jOR-w5BzM](https://youtu.be/e7jOR-w5BzM)**

---

## 🧭 Estratégia de Repositório: Open Core

Para conciliar rigor de verificação técnica pela banca avaliadora da USP e da Claro com a proteção da propriedade intelectual e segredos industriais da solução, o CRIBUM adota uma estrutura **Open Core**:

```
+---------------------------------------------------------------------------------+
|                       CRIBUM REPOSITORY ARCHITECTURE                            |
+---------------------------------------------------------------------------------+
|                                                                                 |
|  [REPOSITÓRIO PÚBLICO: NÚCLEO TÉCNICO DE DEMONSTRAÇÃO (OPEN CORE)]              |
|                                                                                 |
|   1. simulator.html        -> Protótipo mobile PWA 100% offline, áudio nativo,  |
|                               alto contraste Okabe-Ito (9,4:1) e 4 cenários.    |
|   2. cribum_core.py        -> Motor determinístico em Python padrão (zero deps):|
|                               Parser GS1 DataMatrix, Árvore de Merkle RFC 6962, |
|                               fonética LASA PT-BR, trava de dose e suíte forense|
|   3. Documentação Técnica  -> Especificações Claro 5G, FAQ e matriz de tradeoffs|
|                                                                                 |
+---------------------------------------------------------------------------------+
|                                                                                 |
|  [REPOSITÓRIO PRIVADO: INFRAESTRUTURA ENTERPRISE & ADAPTADORES CORPORATIVOS]    |
|                                                                                 |
|   - Pesos finetunados de modelos VLM (Qwen2-VL)                                 |
|   - Microsserviços de integração hospitalar legada (TUSS / ANS / HL7 FHIR)      |
|   - Orquestração distribuída multi-tenant e telemetria de nuvem                 |
|   - Chaves de API, credenciais e configurações de produção                      |
|                                                                                 |
+---------------------------------------------------------------------------------+
```

---

## ⚡ Como Executar e Verificar o Código em Menos de 1 Minuto

O núcleo técnico foi desenhado para **execução imediata, sem necessidade de instalar pacotes externos ou bancos de dados**.

### 1. Testar o Motor Determinístico em Python (Terminal)

O arquivo `cribum_core.py` utiliza exclusivamente a biblioteca padrão do Python (3.9+). Clone o repositório e execute:

```bash
python cribum_core.py
```

O comando executará automaticamente a suíte forense completa:
* **Parser GS1 DataMatrix (ANVISA RDC 319):** validação de GTIN-14 (módulo 10), data de validade (regra dia 00), lote e número de série com separadores de grupo (FNC1 / ASCII 29).
* **Árvore de Merkle RFC 6962:** separação de domínio criptográfico (`0x00` para folhas, `0x01` para nós internos), cálculo de raiz e geração/validação de caminhos de auditoria (Audit Proofs).
* **Motor Fonético LASA PT-BR:** cruzamento de nomes com similaridade fonética e ortográfica (Levenshtein), aplicação de Tall Man Lettering e trava de divergência de dose.
* **Bateria Forense Avançada:** rejeição de ataques de replay inter-árvores, detecção de adulteração de 1 byte no lote (efeito avalanche) e teste de escala com 1.000 folhas processadas em ~13 ms.

### 2. Testar o Protótipo Mobile Interativo (Navegador ou Celular)

O arquivo `simulator.html` é um protótipo mobile completo e autossuficiente:

* **Opção Direta:** Dê dois cliques em `simulator.html` para abrir diretamente no seu navegador.
* **Opção Servidor Local (para testar no celular via Wi-Fi):**

```bash
# Com Node.js:
node serve.js

# Ou com Python:
python -m http.server 8080
```

Abra o endereço indicado no celular ou no navegador desktop e experimente os botões de simulação instantânea no topo da tela.

---

## 🧪 Os 4 Cenários Clínicos Demonstrados

| Cenário de Teste | Prescrição | Caixa Escaneada (GS1 DataMatrix) | Ação do Motor CRIBUM |
| :--- | :--- | :--- | :--- |
| **1. Superdosagem Crítica** | Sulfato de Morfina 10 mg | Sulfato de Morfina 30 mg | **BLOQUEIO IMEDIATO:** Alerta vocal e visual indicando dose 3x maior que a receita. |
| **2. Troca LASA (Grafia/Som)** | Clorpromazina 25 mg (Antipsicótico) | Clomipramina 25 mg (Antidepressivo) | **ALERTA COM DUPLA CONFIRMAÇÃO:** Destaque em Tall Man Lettering (`clorproMAZINA` vs. `clomiPRAMINA`). |
| **3. Homologação Regular** | Humira 40 mg (Adalimumabe) | Humira 40 mg (Lote e serial válidos) | **HOMOLOGAÇÃO:** Selagem criptográfica da folha na Árvore de Merkle e recibo emitido. |
| **4. Fraude por Duplicidade** | Humira 40 mg | Mesma embalagem física já dispensada | **BLOQUEIO ANTIFRAUDE:** Interceptação imediata por colisão de serial na árvore de Merkle. |

---

## 🏛️ Arquitetura Técnica: Separação de Responsabilidades

```
+---------------------------------------------------------------------------------+
| ENTRADA MULTIMODAL NO SMARTPHONE (PWA / OFFLINE-FIRST)                          |
| Receita Digital (QR Code / Texto)  +  GS1 DataMatrix da Caixa (Câmera do Celular)|
+---------------------------------------------------------------------------------+
                                      |
                                      v
+---------------------------------------------------------------------------------+
| CAMADA DE ASSISTÊNCIA COGNITIVA (IA MULTIAGENTE ON-DEVICE)                      |
|                                                                                 |
| - Agente de Leitura: extrai princípio ativo, concentração e AIs do código GS1.  |
| - Agente de Conciliação: normaliza termos para DCB/ANVISA e unifica dosagens.   |
| - Agente de Segurança LASA: analisa proximidade fonética e aplica voz acessível. |
| - Agente de Auditoria: consulta manifesto local e prepara recibo assinado.      |
+---------------------------------------------------------------------------------+
                                      | Dados estruturados (JSON)
                                      v
+---------------------------------------------------------------------------------+
| NÚCLEO DETERMINÍSTICO INVIOLÁVEL (cribum_core.py)                               |
|                                                                                 |
| [X] Trava matemática de divergência de dose (ex.: 30 mg != 10 mg -> BLOQUEIO)  |
| [X] Validação de vigência de validade e dígito verificador GS1 (Módulo 10)      |
| [X] Selagem append-only em Árvore de Merkle RFC 6962                            |
|                                                                                 |
| * REGRA CENTRAL DE SEGURANÇA: A IA auxilia, mas a autoridade de bloqueio        |
|   clínico reside 100% no Núcleo Determinístico imune a alucinações.            |
+---------------------------------------------------------------------------------+
                                      |
                                      v
+---------------------------------------------------------------------------------+
| INTEGRAÇÃO E RECONCILIAÇÃO CLARO 5G                                            |
| Sincronização periódica ultra-rápida de raízes de Merkle entre unidades via MEC |
| e rede Claro 5G Standalone para auditoria forense centralizada contra desvios.   |
+---------------------------------------------------------------------------------+
```

---

## ♿ Tecnologia Assistiva e Acessibilidade (WCAG 2.2 AAA)

* **Paleta Okabe-Ito:** Cores seguras para todos os tipos de daltonismo (deuteranopia, protanopia e tritanopia). Razão de contraste medida de **9,4:1** nos cartões de status (exigência AAA: 7:1).
* **Síntese Vocal Nativa:** Leitura em voz alta de alertas e instruções via Web Speech API nativa, sem consumo de dados e com funcionamento offline.
* **Filtro Anti-Tremor Motor:** Debounce e histerese temporal de 350 ms com alvos de toque generosos (mínimo 60x60 dp) para uso seguro por idosos com tremor essencial ou profissionais em plantões exaustivos.

---

## 📚 Documentação Técnica Complementar

* [`docs/campus_mobile/CAMPUS_MOBILE_PROPOSAL.md`](docs/campus_mobile/CAMPUS_MOBILE_PROPOSAL.md): Proposta técnica detalhada submetida à 15ª Edição do Campus Mobile.
* [`docs/campus_mobile/ARQUITETURA_CLARO_5G.md`](docs/campus_mobile/ARQUITETURA_CLARO_5G.md): Modelo de reconciliação de Merkle Roots e edge computing sobre Claro 5G SA e MEC.
* [`docs/campus_mobile/EDGE_VISION_ROBUSTNESS.md`](docs/campus_mobile/EDGE_VISION_ROBUSTNESS.md): Engenharia óptica para leitura de códigos sob iluminação adversa e ruído.
* [`docs/campus_mobile/TECHNICAL_FAQ_AND_TRADEOFFS.md`](docs/campus_mobile/TECHNICAL_FAQ_AND_TRADEOFFS.md): Perguntas frequentes da banca, matriz CAP e decisões de engenharia.
* [`docs/campus_mobile/ROTEIRO_VALIDACAO_RAPIDA_SUS.md`](docs/campus_mobile/ROTEIRO_VALIDACAO_RAPIDA_SUS.md): Protocolo de validação clínica e usabilidade (NASA-TLX).

---

## 📄 Licença e Propriedade Intelectual

Este projeto está registrado sob a licença **Proprietary & Source-Available Evaluation License**.  
Consulte o arquivo [`LICENSE`](LICENSE) para as condições completas.

* **Permitido:** Avaliação técnica, auditoria de código, clonagem e execução local por comissões avaliadoras de inovação (incluindo o Programa Campus Mobile, Instituto Claro e USP), acadêmicos e recrutadores.
* **Vedado:** Uso comercial não autorizado, exploração em plataformas fechadas de terceiros ou redistribuição sem autorização prévia por escrito do autor.

---

<div align="center">
Desenvolvido por <b>André Rogério da Silva Filho</b><br>
<i>Tecnologia a serviço da integridade humana e da segurança de quem cuida.</i><br>
Contato: <a href="https://www.linkedin.com/in/andre-silvaf">LinkedIn</a> | <a href="https://github.com/TheyDreez">GitHub</a>
</div>
