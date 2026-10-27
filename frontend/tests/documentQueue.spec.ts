import { test, expect } from '@playwright/test';
import { getFriendlyCaseName } from '../src/components/DocumentQueue';

test.describe('DocumentQueue — getFriendlyCaseName unit test suite', () => {
  test('returns friendly case name for mapped synthetic filenames', () => {
    expect(getFriendlyCaseName('caso_01_losartana_lorazepam.jpg')).toBe(
      'Caso 01: Losartana vs Lorazepam (LASA)'
    );
    expect(getFriendlyCaseName('caso_06_sem_crm.jpg')).toBe(
      'Caso 06: Ausência de CRM do Prescritor'
    );
    expect(getFriendlyCaseName('caso_10_posologia_contraditoria.jpg')).toBe(
      'Caso 10: Posologia Contraditória'
    );
    expect(getFriendlyCaseName('caso_20_controle_limpo.jpg')).toBe(
      'Caso 20: Controle Regular 05'
    );
  });

  test('handles case insensitivity for mapped filenames', () => {
    expect(getFriendlyCaseName('CASO_01_LOSARTANA_LORAZEPAM.JPG')).toBe(
      'Caso 01: Losartana vs Lorazepam (LASA)'
    );
    expect(getFriendlyCaseName('Caso_06_Sem_CRM.Jpg')).toBe(
      'Caso 06: Ausência de CRM do Prescritor'
    );
  });

  test('returns original filename as fallback for unmapped filenames', () => {
    expect(getFriendlyCaseName('receita_customizada_123.png')).toBe(
      'receita_customizada_123.png'
    );
    expect(getFriendlyCaseName('documento_desconhecido.pdf')).toBe(
      'documento_desconhecido.pdf'
    );
  });

  test('handles empty string input cleanly', () => {
    expect(getFriendlyCaseName('')).toBe('');
  });
});
