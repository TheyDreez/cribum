# CRIBUM MOBILE: O Escudo de Bolso do SUS contra Erros de Medicamentos e Fraudes

**15ª Edição do Campus Mobile (Instituto Claro • Escola Politécnica da USP • BeOn Claro)**  
*Categoria: Saúde e Tecnologias Assistivas*  
*Autor e Titular:* **André Rogério da Silva Filho**  
*Status:* Protótipo Funcional e Núcleo Tecnológico Concluídos (Fase 1)

---

## 🚨 A Dor Real que o CRIBUM Mobile Resolve na Ponta do SUS

Segundo a Organização Mundial da Saúde (OMS), eventos adversos decorrentes de erros de medicação estão entre as principais causas de danos e mortes evitáveis no mundo, custando mais de 42 bilhões de dólares ao ano.

No cotidiano das Unidades Básicas de Saúde (UBS), farmácias de dispensação do CEAF (Componente Especializado da Assistência Farmacêutica) e hospitais públicos do Brasil, a realidade é dramática:

1. **A Fadiga do Balcão e a Caligrafia Médica:** Farmacêuticos e técnicos de enfermagem enfrentam plantões extenuantes de 12 horas. Sob iluminação fria e pilhas de prescrições manuais com caligrafias ambíguas, a conferência manual falha por cansaço visual.
2. **O Perigo Oculto dos Pares LASA (Look-Alike, Sound-Alike):** Medicamentos com nomes ou sons quase idênticos geram trocas fatais. Entregar *Clorpromazina* (antipsicótico sedativo forte) no lugar de *Clomipramina* (antidepressivo), ou confundir *Losartana* (anti-hipertensivo) com *Lorazepam* (benzodiazepínico depressor do sistema nervoso) leva pacientes idosos à intoxicação grave ou UTI.
3. **O Erro Letal de Dosagem:** Confundir a concentração da mesma droga é fatal. Dispensar *Sulfato de Morfina 30mg* para um paciente com receita de *10mg* representa 300% da dose prescrita, provocando parada respiratória em minutos.
4. **O Rombo dos Medicamentos de Alto Custo (CEAF):** Caixas de remédios de altíssimo custo fornecidas pelo governo, como o *Nusinersena/Spinraza* (mais de R$ 160 mil o frasco) e o *Adalimumabe/Humira* (R$ 3,4 mil), são alvos frequentes de desvios e da fraude de "gasto duplo" (a mesma caixa física é declarada como entregue mais de uma vez para acobertar desvios).
5. **Barreiras Severas de Acessibilidade:** Mais de 8% da população masculina possui algum grau de daltonismo (CVD), e milhares de operadores e pacientes convivem com baixa visão, artrite ou tremores motores involuntários (como Doença de Parkinson e fadiga muscular). Os sistemas atuais do SUS possuem letras miúdas, botões minúsculos e dependem de luz verde/vermelha comum, gerando exclusão e erro humano.

O **CRIBUM Mobile** nasce para transformar qualquer smartphone em um escudo inteligente, multissensorial e acessível, protegendo a vida do paciente e o patrimônio da saúde pública no exato momento da entrega do medicamento.

---

## 📱 O que o CRIBUM Mobile Faz na Mão do Usuário

O aplicativo opera diretamente na câmera do celular com funcionamento **100% offline-first** (não precisa de conexão com a internet para proteger a dispensação na UBS):

* **Leitor Óptico GS1 DataMatrix (ANVISA RDC 319):** A mira laser da câmera captura e decodifica instantaneamente o código bidimensional gravado na caixa do remédio, extraindo GTIN-14, número de série único, lote de fabricação e data de validade normalizada (com suporte à regra do Dia 00).
* **Alerta Bi-Camada Imediato (LASA + Dosagem):** Compara a receita com o medicamento físico. Destaca o padrão internacional *Tall Man Lettering* (letras maiúsculas diferenciadoras recomendadas pelo ISMP Brasil) e bloqueia concentrações divergentes antes que a embalagem seja aberta.
* **Desenho Universal e Tecnologia Assistiva (WCAG 2.2 Nível AAA):**
  * *Paleta Okabe-Ito CVD-Safe:* Substitui o verde e vermelho tradicionais por azul, amarelo-âmbar e vermelhão com contraste acima de 7:1, combinados com formas geométricas redundantes (● Círculo para Homologado, ▲ Triângulo para Alerta e ■ Quadrado para Bloqueio).
  * *Ergonomia Motora (Lei de Fitts):* Alvos de toque expandidos para no mínimo 60dp posicionados no terço inferior da tela (Thumb Zone), permitindo que o profissional opere tudo com uma mão só enquanto segura caixas refrigeradas com a outra.
  * *Escudo Anti-Tremores (Debounce de 350ms):* Amortece micro-toques involuntários típicos de operadores sob exaustão ou pacientes com Parkinson e artrite.
  * *Síntese de Voz (TTS 0.92x) e Feedback Háptico:* O celular vibra em padrões distintos e fala o diagnóstico pausadamente em português, garantindo segurança mesmo sob barulho de posto de saúde ou para quem tem baixa visão.
* **Cofre Criptográfico Offline (Árvore de Merkle RFC 6962):** Cada dispensação gera uma folha criptográfica selada localmente no aparelho. Se alguém tentar escanear a mesma caixa de medicamento de alto custo pela segunda vez, o sistema trava imediatamente por detecção de gasto duplo, gerando um comprovante forense O(log N) que pode ser auditado sem depender de servidores centrais.

---

## 🎮 Como Testar o Protótipo Interativo Agora Mesmo

O protótipo interativo do CRIBUM Mobile roda direto no navegador do celular ou do computador, sem precisar instalar pacotes, extensões ou bancos de dados.

### Abrir o Simulador
Basta abrir o arquivo [simulator.html](simulator.html) no navegador (ou rodar um servidor local com `python -m http.server 8000` e acessar pelo smartphone).

### Os 4 Cenários Clínicos Prontos para a Banca:
1. **Caso 1 (Erro Posológico Crítico):** Prescrição de *Sulfato de Morfina 10mg* vs. Caixa escaneada de *30mg*. O aplicativo dispara o alerta tátil, sonoro e visual de sobredosagem com risco de depressão respiratória.
2. **Caso 2 (Colisão Fonética e Ortográfica LASA):** Prescrição de *Clorpromazina 25mg* vs. Caixa lida de *Clomipramina 25mg*. O aplicativo destaca a diferença em *Tall Man Lettering* (clorPROMAZina vs. cloMIPRAMina) e bloqueia a entrega.
3. **Caso 3 (Dispensação Homologada CEAF + Selagem Merkle):** Caixa de *Adalimumabe 40mg* com serial legítimo. O aplicativo aprova a entrega, gera o hash com prefixo `0x00`, recalcula a raiz da árvore e emite o recibo criptográfico forense.
4. **Caso 4 (Tentativa de Fraude de Gasto Duplo):** Reescaneamento do mesmo número de série do Adalimumabe já dispensado. O aplicativo acusa fraude de duplicidade em tempo real e exibe em qual folha anterior o produto foi baixado.

Também é possível **ativar a câmera traseira do celular** para ver a mira laser e escanear códigos diretamente, além de ligar o modo de alto contraste Okabe-Ito e o filtro anti-tremores.

---

## 🔬 Rigor de Engenharia de Software e Testes

O núcleo do sistema (`cribum_core.py`) foi desenvolvido em Python puro, com zero dependências externas, pronto para rodar em hardware embarcado de baixo custo:

* **Validação de Dígito Módulo-10:** Cálculo matemático estrito para verificação de adulteração em códigos GTIN-14 da ANVISA.
* **Separação Estrita de Domínio (RFC 6962):** Injeção de byte `0x00` para nós folha e byte `0x01` para nós internos, eliminando riscos de colisão e ataques de segunda pré-imagem.
* **Desempenho Assintótico:** Construção de árvore com 1.000 folhas em apenas **13,34 milissegundos** e verificação de prova em **0,0146 milissegundos** (70 vezes mais rápido que o teto de tempo real).
* **Resiliência a Ataques:** Bateria com 100% de aprovação contra ataques de replay de época, adulteração de 1 byte (avalanche) e reuso de serial.

Para executar toda a bateria de testes de auditoria na máquina:
```bash
python cribum_core.py
```

---

## 🏥 Metodologia de Validação de Campo com o SUS

Para garantir que a solução responda à dor real de quem está na linha de frente, o projeto aplica a seguinte dinâmica de escuta com profissionais e usuários:
1. **Profissionais de Farmácia e Enfermagem de UPA/UBS:** Avaliação da clareza do alerta em Tall Man Lettering e da agilidade do leitor óptico durante horários de pico de atendimento.
2. **Pacientes com Baixa Visão e Condições Motoras:** Testes práticos da paleta Okabe-Ito e do escudo anti-tremores com idosos e pessoas com tremores nas mãos para verificar a redução da taxa de cliques acidentais.
3. **Indicadores de Sucesso Medidos:**
   * Redução a zero de trocas de medicamentos entre pares LASA catalogados.
   * Tempo de conferência por item inferior a 3 segundos.
   * Taxa de amortecimento de toques involuntários superior a 90% em usuários com tremor essencial.

---

## 🌐 Conexão com o Ecossistema Claro e Redes 5G

O CRIBUM Mobile foi arquitetado para aproveitar ao máximo a infraestrutura de telecomunicações móveis:
* **Modo Isolado (Borda Offline):** Em postos rurais, unidades fluviais ou em momentos de instabilidade de rede, toda a validação clínica e a assinatura na árvore de Merkle ocorrem localmente no processador do smartphone.
* **Sincronização Claro 5G Standalone (URLLC):** Onde houver cobertura Claro 5G, as raízes criptográficas locais são sincronizadas com a central sanitária estadual via fatiamento de rede dedicado (5QI 82), garantindo latência abaixo de 10ms para impedir que uma carga desviada em um município seja dispensada em outro.

---

## 📂 Mapa do Repositório

* `simulator.html`: Simulador interativo do aplicativo móvel com leitor óptico, Tecnologia Assistiva WCAG 2.2 AAA e motor criptográfico WebCrypto.
* `cribum_core.py`: Núcleo matemático e clínico em Python puro com parsers ANVISA, Árvores de Merkle RFC 6962 e suíte de testes unitários.
* `CAMPUS_MOBILE_PROPOSAL.md`: Dossiê oficial e formal da proposta submetida para o Campus Mobile 15ª Edição.
* `TECHNICAL_FAQ_AND_TRADEOFFS.md`: Análise de decisões de engenharia, Teorema CAP e justificativas de trade-offs.
* `EDGE_VISION_ROBUSTNESS.md`: Especificação de visão computacional na borda sob iluminação precária e condensação de cadeia de frio.
* `ARQUITETURA_CLARO_5G.md`: Especificação técnica de conectividade, fatiamento de rede Claro 5G e modelo B2Gov para o SUS.
* `GUIA_GRAVACAO_PITCH_90S.md`: Roteiro estruturado segundo a segundo para a gravação do vídeo pitch de apresentação.