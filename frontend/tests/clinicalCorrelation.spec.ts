import { test, expect } from '@playwright/test';
import { evaluateHypothesisClinicalMatch } from '../src/clinicalCorrelation';

test.describe('evaluateHypothesisClinicalMatch — Unit Tests', () => {
  test.describe('COMPATIBLE status scenarios', () => {
    test('returns COMPATIBLE when drug is compatible with document CID (e.g. Losartana for I10)', () => {
      const result = evaluateHypothesisClinicalMatch('CASE-AMB-001', 'losartana 50mg');

      expect(result.status).toBe('COMPATIBLE');
      expect(result.badgeLabel).toBe('Compatível com Diagnóstico I10');
      expect(result.therapeuticClass).toBe('Anti-hipertensivo (BRA)');
      expect(result.cidContext).toEqual({
        cid: 'I10',
        description: 'Hipertensão Essencial Primária',
        expectedClasses: ['Anti-hipertensivo (BRA)', 'Diurético Tiazídico'],
      });
      expect(result.lasaWarning).toContain('ISMP Brasil: Risco de sedação profunda');
    });

    test('returns COMPATIBLE when drug is compatible with document CID (e.g. Digoxina for I50)', () => {
      const result = evaluateHypothesisClinicalMatch('CASE-AMB-003', 'Digoxina 0.25mg');

      expect(result.status).toBe('COMPATIBLE');
      expect(result.badgeLabel).toBe('Compatível com Diagnóstico I50');
      expect(result.therapeuticClass).toBe('Glicosídeo Cardíaco (Alta Vigilância)');
      expect(result.cidContext?.cid).toBe('I50');
      expect(result.lasaWarning).toContain('ISMP Brasil: Medicamento de índice terapêutico estreito');
    });

    test('returns COMPATIBLE with null lasaWarning when drug has no LASA alert (e.g. Dipirona for M54.5)', () => {
      const result = evaluateHypothesisClinicalMatch('CASE-AMB-005', 'dipirona 500mg');

      expect(result.status).toBe('COMPATIBLE');
      expect(result.badgeLabel).toBe('Compatível com Diagnóstico M54.5');
      expect(result.therapeuticClass).toBe('Analgésico e Antipirético');
      expect(result.cidContext?.cid).toBe('M54.5');
      expect(result.lasaWarning).toBeNull();
    });
  });

  test.describe('DISCREPANT status scenarios', () => {
    test('returns DISCREPANT when drug is not compatible with document CID (e.g. Lorazepam for I10)', () => {
      const result = evaluateHypothesisClinicalMatch('CASE-AMB-001', 'lorazepam 2mg');

      expect(result.status).toBe('DISCREPANT');
      expect(result.badgeLabel).toBe('Discrepância Diagnóstica (I10)');
      expect(result.therapeuticClass).toBe(
        'Benzodiazepínico (Ansiolítico) — sem indicação primária para I10'
      );
      expect(result.cidContext?.cid).toBe('I10');
      expect(result.lasaWarning).toContain('ISMP Brasil: Em paciente hipertenso (CID I10)');
    });

    test('returns DISCREPANT for Flunarizina in depression context (F32.1)', () => {
      const result = evaluateHypothesisClinicalMatch('CASE-AMB-002', 'flunarizina 10mg');

      expect(result.status).toBe('DISCREPANT');
      expect(result.badgeLabel).toBe('Discrepância Diagnóstica (F32.1)');
      expect(result.therapeuticClass).toBe(
        'Bloqueador de Canal de Cálcio / Antivertiginoso — sem indicação primária para F32.1'
      );
      expect(result.cidContext?.cid).toBe('F32.1');
      expect(result.lasaWarning).toContain('ISMP Brasil: Contraindicado em quadros depressivos');
    });
  });

  test.describe('NEUTRAL status scenarios', () => {
    test('returns NEUTRAL when docId is unknown but drug is matched', () => {
      const result = evaluateHypothesisClinicalMatch('UNKNOWN-DOC-999', 'losartana 50mg');

      expect(result.status).toBe('NEUTRAL');
      expect(result.badgeLabel).toBe('Avaliação Clínica Manual');
      expect(result.therapeuticClass).toBe('Anti-hipertensivo (BRA)');
      expect(result.cidContext).toBeNull();
      expect(result.lasaWarning).toContain('ISMP Brasil: Risco de sedação profunda');
    });

    test('returns NEUTRAL when docId is known but hypothesis drug is unmatched', () => {
      const result = evaluateHypothesisClinicalMatch('CASE-AMB-001', 'paracetamol 500mg');

      expect(result.status).toBe('NEUTRAL');
      expect(result.badgeLabel).toBe('Avaliação Clínica Manual');
      expect(result.therapeuticClass).toBe('Verificação pericial padrão');
      expect(result.cidContext?.cid).toBe('I10');
      expect(result.lasaWarning).toBeNull();
    });

    test('returns NEUTRAL when both docId and drug are unknown', () => {
      const result = evaluateHypothesisClinicalMatch('UNKNOWN-DOC-999', 'remedio_desconhecido');

      expect(result.status).toBe('NEUTRAL');
      expect(result.badgeLabel).toBe('Avaliação Clínica Manual');
      expect(result.therapeuticClass).toBe('Verificação pericial padrão');
      expect(result.cidContext).toBeNull();
      expect(result.lasaWarning).toBeNull();
    });
  });

  test.describe('Edge cases and input robustness', () => {
    test('handles UPPERCASE and MixedCase hypothesis text', () => {
      const upperResult = evaluateHypothesisClinicalMatch('CASE-AMB-001', 'LOSARTANA 50MG');
      expect(upperResult.status).toBe('COMPATIBLE');

      const mixedResult = evaluateHypothesisClinicalMatch('CASE-AMB-002', 'FluOxEtiNa 20mg');
      expect(mixedResult.status).toBe('COMPATIBLE');
    });

    test('matches keyword embedded in full sentence with spaces and punctuation', () => {
      const sentenceResult = evaluateHypothesisClinicalMatch(
        'CASE-AMB-005',
        'Uso contínuo de Tramadol 50mg VO de 8/8h para dor lombar.'
      );
      expect(sentenceResult.status).toBe('COMPATIBLE');
      expect(sentenceResult.cidContext?.cid).toBe('M54.5');
      expect(sentenceResult.therapeuticClass).toBe('Opioide Analgésico');
    });

    test('handles empty string gracefully without throwing errors', () => {
      const result = evaluateHypothesisClinicalMatch('CASE-AMB-001', '');

      expect(result.status).toBe('NEUTRAL');
      expect(result.badgeLabel).toBe('Avaliação Clínica Manual');
      expect(result.therapeuticClass).toBe('Verificação pericial padrão');
      expect(result.cidContext?.cid).toBe('I10');
      expect(result.lasaWarning).toBeNull();
    });

    test('handles null/falsy hypothesis text gracefully without throwing errors', () => {
      const result = evaluateHypothesisClinicalMatch(
        'CASE-AMB-001',
        null as unknown as string
      );

      expect(result.status).toBe('NEUTRAL');
      expect(result.badgeLabel).toBe('Avaliação Clínica Manual');
      expect(result.therapeuticClass).toBe('Verificação pericial padrão');
      expect(result.cidContext?.cid).toBe('I10');
      expect(result.lasaWarning).toBeNull();
    });
  });
});
