# GUIA PRÁTICO: NARRATIVA ENXUTA E VALIDAÇÃO RÁPIDA COM PROFISSIONAIS DE SAÚDE
**Projeto:** CRIBUM Mobile (15ª Edição Campus Mobile, Categoria Saúde e Tecnologias Assistivas)

---

## 1. A DEFINIÇÃO CENTRAL DO PRODUTO (PARA A INSCRIÇÃO E BANCA)

Use sempre esta frase-tese como abertura em todos os campos da inscrição (evitando jogar 7 tecnologias diferentes de uma vez):

> **"O CRIBUM Mobile é uma plataforma mobile de segurança na dispensação de medicamentos que combina inteligência artificial multiagente, validação determinística e rastreabilidade criptográfica para prevenir erros clínicos e irregularidades no SUS."**

### Hierarquia Clara do Produto:
* **Núcleo do produto (o que resolve em 15 segundos amanhã de manhã):** Segurança na dispensação de medicamentos no balcão da farmácia pública e em casa (impedir entrega de dose errada como `Morfina 30 mg vs. 10 mg` e troca de nomes parecidos como `Clorpromazina vs. Clomipramina`).
* **Diferencial complementar 1 (Integridade para o gestor público):** Registro criptográfico *offline-first* em Árvore de Merkle para evitar dispensação duplicada na unidade, com sincronização e reconciliação compartilhada entre unidades quando há rede 5G.
* **Diferencial complementar 2 (Inclusão assistiva):** Modo de linguagem simples com alerta em voz alta para idosos com baixa visão e modo de alto contraste com filtro anti-tremor.

---

## 2. O FLUXO LINEAR DE 6 PASSOS (COMO EXPLICAR O FUNCIONAMENTO)

Sempre descreva o CRIBUM Mobile seguindo esta linha reta de 6 etapas:

1. **Prescrição:** O profissional ou paciente apresenta a Receita Digital do SUS (QR Code ou texto).
2. **Interpretação (Agentes On-Device):** Os agentes de Leitura e Conciliação extraem o princípio ativo, a concentração (`mg/mL`) e a posologia, normalizando pelos nomes oficiais da ANVISA (DCB).
3. **Leitura da Embalagem:** A câmera do celular lê o código bidimensional GS1 DataMatrix da caixa física na mão do usuário.
4. **Validação (Núcleo Determinístico + Agente LASA):** O motor determinístico confronta matematicamente princípio ativo, concentração e validade, enquanto o agente LASA verifica similaridade fonética/ortográfica. *(A IA nunca aprova uma entrega sozinha; o bloqueio é 100% determinístico).*
5. **Decisão Assistida:** A tela e a síntese de voz aprovam a entrega (verde/azul), exigem dupla checagem (laranja) ou bloqueiam imediatamente a superdosagem/duplicidade (vermelho).
6. **Registro e Sincronização:** A entrega homologada é gravada na Árvore de Merkle local da unidade (funcionando mesmo sem internet) e, quando o aparelho se conecta à rede 5G, os registros são sincronizados e reconciliados entre as unidades de saúde.

---

## 3. COMO CONSEGUIR VALIDAÇÃO EXTERNA REAL EM 15 MINUTOS (WHATSAPP / BALCÃO)

O ponto mais importante apontado na crítica para aumentar sua nota no critério **Impacto (Peso 3)** é ter pelo menos **1 a 3 avaliações reais de farmacêuticos, técnicos de farmácia/enfermagem ou gestores de UBS**.

Você pode conseguir isso hoje mesmo mandando o vídeo de 80 segundos (ou mostrando o `simulator.html` aberto no seu celular) para qualquer farmacêutico (de UBS, hospital ou mesmo de drogaria na sua rua) com esta mensagem curta:

### Mensagem pronta para enviar no WhatsApp ou abordar um farmacêutico:
```text
Oi [Nome], tudo bem? Estou inscrevendo um projeto de segurança de medicamentos na 15ª Edição do Campus Mobile (USP / Instituto Claro) chamado CRIBUM Mobile.

É um web app que funciona offline no celular para conferir a Receita Digital contra o código DataMatrix da caixa antes da entrega, bloqueando na hora troca de nomes parecidos (tipo Clorpromazina vs Clomipramina) e erro de concentração (tipo 30 mg no lugar de 10 mg).

Como você atua na área, você consegue ver esse vídeo de 1 minutinho e me responder 3 perguntas rápidas para eu registrar como validação profissional no projeto?

1. Na rotina real de balcão/plantão, qual o maior risco de confusão entre caixas parecidas ou concentrações diferentes?
2. Um bloqueio visual e sonoro direto na câmera do celular em menos de 3 segundos ajudaria na conferência?
3. Posso citar seu nome/cargo (ex: "Validado em entrevista preliminar com [Nome], Farmacêutico CRF-XX") como feedback técnico na inscrição?
```

Assim que 1 ou 2 profissionais responderem, basta incluir uma linha no seu texto de inscrição:
> *"Protótipo submetido à avaliação preliminar com profissionais de farmácia/enfermagem ([inserir cargo/CRF]), que validaram a aderência dos bloqueios de concentração (10 mg vs. 30 mg) e pares LASA (Clorpromazina vs. Clomipramina) à rotina real de dispensação."*
