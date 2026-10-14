export interface ClinicalDiagnosisContext {
  cid: string;
  description: string;
  expectedClasses: string[];
}

export interface DrugClinicalProfile {
  keyword: string;
  therapeuticClass: string;
  primaryIndication: string;
  compatibleCids: string[];
  lasaAlert?: {
    pairCode: string;
    confusedWith: string;
    ismpRisk: string;
  };
}

// Mapeamento dos contextos clínicos de referência das guias do catálogo (Ground Truth)
export const DOCUMENT_CID_CONTEXT: Record<string, ClinicalDiagnosisContext> = {
  'CASE-AMB-001': {
    cid: 'I10',
    description: 'Hipertensão Essencial (Primária)',
    expectedClasses: ['Anti-hipertensivo (BRA)', 'Diurético Tiazídico'],
  },
  'CASE-AMB-002': {
    cid: 'F32.1',
    description: 'Episódio Depressivo Moderado',
    expectedClasses: ['Antidepressivo (ISRS)'],
  },
  'CASE-AMB-003': {
    cid: 'I50',
    description: 'Insuficiência Cardíaca',
    expectedClasses: ['Glicosídeo Cardíaco', 'Cardiotônico'],
  },
  'CASE-AMB-004': {
    cid: 'F41.1',
    description: 'Ansiedade Generalizada',
    expectedClasses: ['Antidepressivo (ISRS)'],
  },
  'CASE-AMB-005': {
    cid: 'M54.5',
    description: 'Dor Lombar Baixa (Lombalgia)',
    expectedClasses: ['Opioide Analgésico', 'Analgésico'],
  },
  'CASE-INC-009': {
    cid: 'J00',
    description: 'Nasofaringite Aguda (Resfriado Comum)',
    expectedClasses: ['Sintomático Respiratório'],
  },
};

export const DRUG_CLINICAL_DATABASE: DrugClinicalProfile[] = [
  {
    keyword: 'losartana',
    therapeuticClass: 'Anti-hipertensivo (BRA)',
    primaryIndication: 'Hipertensão arterial sistêmica e insuficiência cardíaca',
    compatibleCids: ['I10', 'I50'],
    lasaAlert: {
      pairCode: 'LASA-001',
      confusedWith: 'Lorazepam 2mg',
      ismpRisk:
        'ISMP Brasil: Risco de sedação profunda indevida, depressão respiratória ou crise hipertensiva aguda por suspensão abrupta do anti-hipertensivo.',
    },
  },
  {
    keyword: 'lorazepam',
    therapeuticClass: 'Benzodiazepínico (Ansiolítico)',
    primaryIndication: 'Ansiedade aguda severa e insônia',
    compatibleCids: ['F41.1'],
    lasaAlert: {
      pairCode: 'LASA-001',
      confusedWith: 'Losartana 50mg',
      ismpRisk:
        'ISMP Brasil: Em paciente hipertenso (CID I10), a dispensação acidental de Lorazepam causa sonolência grave, risco de queda e descontrole pressórico.',
    },
  },
  {
    keyword: 'fluoxetina',
    therapeuticClass: 'Antidepressivo (ISRS)',
    primaryIndication: 'Transtorno depressivo maior (CID F32.1)',
    compatibleCids: ['F32.1', 'F41.1'],
    lasaAlert: {
      pairCode: 'LASA-003',
      confusedWith: 'Flunarizina 10mg',
      ismpRisk:
        'ISMP Brasil: Risco de agravamento de depressão induzido por Flunarizina em pacientes psiquiátricos e parkinsonismo medicamentoso.',
    },
  },
  {
    keyword: 'flunarizina',
    therapeuticClass: 'Bloqueador de Canal de Cálcio / Antivertiginoso',
    primaryIndication: 'Profilaxia de vertigem vestibular e enxaqueca',
    compatibleCids: ['H81', 'G43'],
    lasaAlert: {
      pairCode: 'LASA-003',
      confusedWith: 'Fluoxetina 20mg',
      ismpRisk:
        'ISMP Brasil: Contraindicado em quadros depressivos (CID F32.1) por induzir sintomas depressivos e extrapiramidais.',
    },
  },
  {
    keyword: 'digoxina',
    therapeuticClass: 'Glicosídeo Cardíaco (Alta Vigilância)',
    primaryIndication: 'Insuficiência cardíaca (CID I50) e fibrilação atrial',
    compatibleCids: ['I50', 'I48'],
    lasaAlert: {
      pairCode: 'LASA-004',
      confusedWith: 'Dipirona 500mg',
      ismpRisk:
        'ISMP Brasil: Medicamento de índice terapêutico estreito. Troca de dose com Dipirona ocasiona intoxicação digitálica potencialmente fatal.',
    },
  },
  {
    keyword: 'dipirona',
    therapeuticClass: 'Analgésico e Antipirético',
    primaryIndication: 'Dor aguda e febre (CID J06.9)',
    compatibleCids: ['J06.9', 'M54.5', 'R50'],
  },
  {
    keyword: 'citalopram',
    therapeuticClass: 'Antidepressivo (ISRS)',
    primaryIndication: 'Transtorno depressivo e ansiedade (Dose usual 20mg-40mg)',
    compatibleCids: ['F41.1', 'F32.1'],
    lasaAlert: {
      pairCode: 'LASA-002',
      confusedWith: 'Escitalopram 10mg',
      ismpRisk:
        'ISMP Brasil: Escitalopram possui potência 2x superior por miligrama. Risco de sobredosagem serotoninérgica ou subdose.',
    },
  },
  {
    keyword: 'escitalopram',
    therapeuticClass: 'Antidepressivo (ISRS - Enantiômero S)',
    primaryIndication: 'Ansiedade e depressão (Potência 2x em relação ao Citalopram)',
    compatibleCids: ['F41.1', 'F32.1'],
  },
  {
    keyword: 'tramadol',
    therapeuticClass: 'Opioide Analgésico',
    primaryIndication: 'Dor moderada a severa (CID M54.5)',
    compatibleCids: ['M54.5'],
    lasaAlert: {
      pairCode: 'LASA-006',
      confusedWith: 'Trazodona 50mg',
      ismpRisk:
        'ISMP Brasil: Troca acidental entre Tramadol e Trazodona causa sedação excessiva, hipotensão ortostática e falha analgésica.',
    },
  },
  {
    keyword: 'trazodona',
    therapeuticClass: 'Antidepressivo Sedativo',
    primaryIndication: 'Depressão com insônia associada',
    compatibleCids: ['F32.1', 'G47.0'],
  },
];

export function evaluateHypothesisClinicalMatch(
  docId: string,
  hypothesisText: string
): {
  status: 'COMPATIBLE' | 'DISCREPANT' | 'NEUTRAL';
  badgeLabel: string;
  therapeuticClass: string;
  cidContext: ClinicalDiagnosisContext | null;
  lasaWarning: string | null;
} {
  const cidContext = DOCUMENT_CID_CONTEXT[docId] || null;
  const normalized = (hypothesisText || '').toLowerCase();

  const matchedDrug = DRUG_CLINICAL_DATABASE.find((d) =>
    normalized.includes(d.keyword)
  );

  if (!matchedDrug || !cidContext) {
    return {
      status: 'NEUTRAL',
      badgeLabel: 'Avaliação Clínica Manual',
      therapeuticClass: matchedDrug?.therapeuticClass || 'Verificação pericial padrão',
      cidContext,
      lasaWarning: matchedDrug?.lasaAlert?.ismpRisk || null,
    };
  }

  const isCompatible = matchedDrug.compatibleCids.includes(cidContext.cid);

  if (isCompatible) {
    return {
      status: 'COMPATIBLE',
      badgeLabel: `Compatível com Diagnóstico ${cidContext.cid}`,
      therapeuticClass: matchedDrug.therapeuticClass,
      cidContext,
      lasaWarning: matchedDrug.lasaAlert?.ismpRisk || null,
    };
  }

  return {
    status: 'DISCREPANT',
    badgeLabel: `Discrepância Diagnóstica (${cidContext.cid})`,
    therapeuticClass: `${matchedDrug.therapeuticClass} — sem indicação primária para ${cidContext.cid}`,
    cidContext,
    lasaWarning: matchedDrug.lasaAlert?.ismpRisk || null,
  };
}
