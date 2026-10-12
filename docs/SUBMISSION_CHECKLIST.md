# CHECKLIST DE SUBMISSÃO — AMD DEVELOPER HACKATHON: ACT III

**Prazo Fatal de Entrega:** 18 de Outubro de 2026 às 15:00 UTC (12:00 BRT).  
**Plataforma de Submissão:** [lablab.ai/ai-hackathons/amd-developer-hackathon-act-iii](https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-iii)  
**Trilha:** `Health and Wellbeing`  

---

## 1. Requisitos de Código e Repositório

- [x] Repositório Git com branches e histórico de commits incrementais.
- [x] Licença open-source permissiva (MIT) incluída no arquivo `LICENSE`.
- [x] `.env.example` sem credenciais, senhas ou tokens sensíveis.
- [x] Testes automatizados passando (`pytest backend/tests/test_api.py`).
- [x] Build de frontend sem erros de compilação TypeScript (`npm run build`).
- [ ] **Ação no dia da entrega:** Alterar a visibilidade do repositório no GitHub de privado para **público** (`gh repo edit TheyDreez/cribum --visibility public`).

---

## 2. Requisitos de Evidência de Tecnologia AMD

- [x] Adaptador de inferência vLLM/ROCm implementado sem fallback silencioso (`RealROCmProvider`).
- [x] Arquivo de configuração Docker para o contêiner AMD (`docker/docker-compose.rocm.yml`).
- [x] Guia de provisionamento e reprodução técnica documentado em `docs/AMD_SETUP.md`.
- [ ] **Ação no teste de hardware:** Gravação de tela curta ou captura do comando `rocm-smi` exibindo o consumo de VRAM e processamento da GPU AMD.

---

## 3. Bloco de Avaliação Obrigatório da Trilha de Saúde

Campos textuais que devem constar na descrição da submissão:
1. **One Business Result:** Redução de até 80% no tempo de triagem de guias com caligrafia ambígua e 100% de interceptação de conflitos LASA críticos antes da dispensação.
2. **One Known Limitation:** A pontuação percentual das hipóteses é heurística e não calibrada; requer supervisão humana para medicamentos com janelas terapêuticas estreitas.
3. **One Failure Case (O Caso de Dúvida):** Caligrafia cursiva sobreposta onde *Losartana 50mg* e *Lorazepam 2mg* possuem traçado idêntico.
4. **The Safeguard / Human Review Process:** O sistema bloqueia a aprovação autônoma, gera badge de incerteza em âmbar e exige a assinatura e fundamentação de um auditor humano na interface.

---

## 4. Materiais Multimídia de Apresentação

- [ ] Gravação do vídeo de demonstração (3 minutos) seguindo o roteiro `docs/DEMO_SCRIPT.md`.
- [ ] Upload do vídeo no YouTube (Não listado ou público) ou Vimeo.
- [ ] Apresentação em slides (Pitch deck de até 10 slides).
- [ ] Imagem de capa (Banner com a identidade visual da fábrica têxtil / tear de Sorocaba).
