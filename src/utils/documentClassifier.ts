import { DocumentType, DocumentTypeInfo } from "@/types/document";

/**
 * Classify document type based on content analysis
 */
export const classifyDocument = (text: string): DocumentTypeInfo => {
  const lowerText = text.toLowerCase();
  
  // Legal petition keywords
  const legalKeywords = [
    "excelentíssimo",
    "meritíssimo",
    "comarca",
    "processo",
    "autor",
    "réu",
    "petição",
    "vara",
    "juízo",
    "defesa",
    "ação",
    "sentença",
  ];

  // Contract keywords
  const contractKeywords = [
    "contratante",
    "contratado",
    "cláusula",
    "partes",
    "acordo",
    "vigência",
    "rescisão",
    "testemunhas",
    "assinam",
  ];

  // Invoice keywords
  const invoiceKeywords = [
    "nota fiscal",
    "nf-e",
    "cnpj",
    "valor total",
    "impostos",
    "icms",
    "ipi",
    "emitente",
    "destinatário",
    "danfe",
  ];

  // Resume keywords
  const resumeKeywords = [
    "currículo",
    "experiência profissional",
    "formação acadêmica",
    "habilidades",
    "objetivo",
    "qualificações",
    "telefone",
    "e-mail",
  ];

  // ID document keywords
  const idKeywords = [
    "rg",
    "cpf",
    "carteira de identidade",
    "certidão",
    "nascimento",
    "órgão expedidor",
    "data de emissão",
    "nacionalidade",
  ];

  // Receipt keywords
  const receiptKeywords = [
    "recibo",
    "recebi",
    "valor de",
    "referente",
    "pagamento",
    "quitação",
    "por extenso",
  ];

  // Report keywords
  const reportKeywords = [
    "relatório",
    "análise",
    "conclusão",
    "resultados",
    "metodologia",
    "introdução",
    "sumário",
    "referências",
  ];

  // Payslip keywords (NEW)
  const payslipKeywords = [
    "contracheque",
    "holerite",
    "folha de pagamento",
    "salário bruto",
    "salário líquido",
    "descontos",
    "inss",
    "fgts",
    "irrf",
    "vale transporte",
    "vale alimentação",
  ];

  // Personnel file keywords (NEW)
  const personnelFileKeywords = [
    "ficha",
    "cadastro",
    "dados pessoais",
    "admissão",
    "demissão",
    "cargo",
    "função",
    "departamento",
    "matrícula",
    "colaborador",
  ];

  // Timecard keywords (NEW)
  const timecardKeywords = [
    "cartão ponto",
    "registro de ponto",
    "entrada",
    "saída",
    "intervalo",
    "horas trabalhadas",
    "horas extras",
    "banco de horas",
    "jornada",
  ];

  // Count keyword matches
  const scores = {
    legal_petition: countMatches(lowerText, legalKeywords),
    contract: countMatches(lowerText, contractKeywords),
    invoice: countMatches(lowerText, invoiceKeywords),
    resume: countMatches(lowerText, resumeKeywords),
    id_document: countMatches(lowerText, idKeywords),
    receipt: countMatches(lowerText, receiptKeywords),
    report: countMatches(lowerText, reportKeywords),
    payslip: countMatches(lowerText, payslipKeywords),
    personnel_file: countMatches(lowerText, personnelFileKeywords),
    timecard: countMatches(lowerText, timecardKeywords),
  };

  // Find type with highest score
  const entries = Object.entries(scores) as [DocumentType, number][];
  const [topType, topScore] = entries.reduce((a, b) => (b[1] > a[1] ? b : a));

  // Calculate confidence based on score
  const confidence = Math.min(95, Math.max(30, topScore * 15));

  const labels: Record<DocumentType, string> = {
    legal_petition: "Petição Jurídica",
    contract: "Contrato",
    invoice: "Nota Fiscal",
    resume: "Currículo",
    id_document: "Documento de Identidade",
    receipt: "Recibo",
    report: "Relatório",
    letter: "Carta/Ofício",
    form: "Formulário",
    payslip: "Contracheque",
    personnel_file: "Ficha de Pessoal",
    timecard: "Cartão Ponto",
    other: "Documento Geral",
  };

  const icons: Record<DocumentType, string> = {
    legal_petition: "⚖️",
    contract: "📝",
    invoice: "🧾",
    resume: "👤",
    id_document: "🪪",
    receipt: "🧾",
    report: "📊",
    letter: "✉️",
    form: "📋",
    payslip: "💰",
    personnel_file: "📁",
    timecard: "⏰",
    other: "📄",
  };

  // If confidence is too low, classify as "other"
  const finalType = confidence > 40 ? topType : "other";

  return {
    type: finalType,
    confidence: Math.round(confidence),
    label: labels[finalType],
    icon: icons[finalType],
  };
};

/**
 * Count how many keywords are present in text
 */
const countMatches = (text: string, keywords: string[]): number => {
  return keywords.filter((keyword) => text.includes(keyword)).length;
};

/**
 * Detect primary language of text
 */
export const detectLanguage = (text: string): string => {
  const lowerText = text.toLowerCase();

  // Portuguese indicators
  const ptIndicators = [
    "ação",
    "não",
    "são",
    "está",
    "então",
    "também",
    "muito",
    "mais",
    "como",
    "será",
    "português",
    "informação",
  ];

  // English indicators
  const enIndicators = [
    "the",
    "and",
    "this",
    "that",
    "with",
    "from",
    "have",
    "will",
    "information",
    "company",
  ];

  // Spanish indicators
  const esIndicators = [
    "que",
    "con",
    "para",
    "está",
    "como",
    "más",
    "también",
    "información",
    "español",
  ];

  const ptScore = countMatches(lowerText, ptIndicators);
  const enScore = countMatches(lowerText, enIndicators);
  const esScore = countMatches(lowerText, esIndicators);

  if (ptScore >= enScore && ptScore >= esScore) return "pt-BR";
  if (enScore > ptScore && enScore >= esScore) return "en";
  if (esScore > ptScore && esScore > enScore) return "es";

  return "pt-BR"; // Default to Portuguese
};
