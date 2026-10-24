# CRIBUM MOBILE: Escudo Clínico e Antifraude do SUS
**15ª Edição do Campus Mobile (Instituto Claro | Escola Politécnica da USP | BeOn Claro)**  
*Categoria: Saúde e Tecnologias Assistivas*  
*Autor e Titular:* **André Rogério da Silva Filho**

---

## 📌 Visão Geral do Projeto
O **Cribum Mobile** transforma smartphones comuns em estações forenses de verificação farmacêutica e segurança do paciente no SUS, funcionando de forma **100% offline-first**.

### Os 3 Pilares Tecnológicos:
1. **Parser GS1 DataMatrix (ANVISA SNCM):** Decodifica e valida os identificadores regulamentares `(01)` GTIN-14 com dígito Módulo 10, `(21)` Serial individualizado, `(17)` Validade (com regra de dia 00) e `(10)` Lote.
2. **Ledger Criptográfico Offline em Árvore de Merkle (RFC 6962):** Registro append-only com separação de domínio que bloqueia tentativas de dupla dispensação de medicamentos de alto custo (CEAF) mesmo sem nenhuma conexão à internet na UBS.
3. **Escudo Clínico Bi-Camada (LASA PT-BR + Posologia Estrita):**
   - *Camada 1 (Princípio Ativo):* Fonetização PT-BR (vocalização de L, dígrafos farmacêuticos) e geração automática de *Tall Man Lettering* (ISMP Brasil / ANVISA) contra trocas de nomes semelhantes.
   - *Camada 2 (Posologia Estrita):* Extração e normalização de grandezas (`1g` $\equiv$ `1000mg`), bloqueando instantaneamente discrepâncias fatais de dosagem (ex.: prescrito 10mg vs dispensado 30mg).
4. **Privacidade LGPD:** Hashing HMAC-SHA256 do CPF salgado com o CNES do posto de saúde.

---

## 🚀 Como Executar os Testes do Núcleo
O núcleo `cribum_core.py` foi implementado em Python puro (zero dependências externas), otimizado para dispositivos móveis e sistemas embarcados.

Para rodar a suíte completa de testes automatizados:
```bash
uv run python cribum_core.py
```

---

## 📂 Estrutura de Arquivos
* `cribum_core.py`: Implementação completa dos 3 motores e testes unitários/integração.
* `simulator.html`: Simulador visual interativo de smartphone para demonstração e pitch.
* `CAMPUS_MOBILE_PROPOSAL.md`: Dossiê oficial para submissão (Resumo, Problema, Solução, Métricas, Sinergia com Claro 5G e Roteiro do Vídeo Pitch de 90s).
