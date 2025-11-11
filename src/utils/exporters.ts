import { ProcessedDocument, PageResult } from "@/types/document";

/**
 * Export to plain text
 */
export const exportToTxt = (doc: ProcessedDocument): Blob => {
  let text = `Strukturis - Documento Processado\n`;
  text += `Processado em: ${doc.processedAt.toLocaleString("pt-BR")}\n`;
  text += `Confiabilidade geral: ${doc.overallConfidence}%\n`;
  text += `Total de páginas: ${doc.totalPages}\n`;
  text += `\n${"=".repeat(60)}\n\n`;

  doc.pages.forEach((page) => {
    text += `\n--- Página ${page.pageNumber} (Confiabilidade: ${page.confidence}%) ---\n\n`;
    text += page.text;
    text += "\n\n";
  });

  return new Blob([text], { type: "text/plain;charset=utf-8" });
};

/**
 * Export to CSV (for tables)
 */
export const exportToCsv = (doc: ProcessedDocument): Blob => {
  let csv = "";

  doc.pages.forEach((page) => {
    if (page.hasTable && page.tableData) {
      csv += `Página ${page.pageNumber}\n`;
      page.tableData.forEach((row) => {
        csv += row.map((cell) => `"${cell.replace(/"/g, '""')}"`).join(",") + "\n";
      });
      csv += "\n";
    }
  });

  if (!csv) {
    csv = "Nenhuma tabela detectada no documento.\n";
  }

  return new Blob([csv], { type: "text/csv;charset=utf-8" });
};

/**
 * Export to JSON
 */
export const exportToJson = (doc: ProcessedDocument): Blob => {
  const data = {
    document: {
      fileName: doc.originalFile.name,
      processedAt: doc.processedAt.toISOString(),
      overallConfidence: doc.overallConfidence,
      totalPages: doc.totalPages,
    },
    pages: doc.pages.map((page) => ({
      pageNumber: page.pageNumber,
      text: page.text,
      confidence: page.confidence,
      hasTable: page.hasTable,
      tableData: page.tableData || null,
      segments: page.segments,
    })),
  };

  const jsonString = JSON.stringify(data, null, 2);
  return new Blob([jsonString], { type: "application/json;charset=utf-8" });
};

/**
 * Export to HTML
 */
export const exportToHtml = (doc: ProcessedDocument): Blob => {
  let html = `<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${doc.originalFile.name} - Strukturis</title>
  <style>
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      max-width: 900px;
      margin: 40px auto;
      padding: 20px;
      line-height: 1.6;
      background-color: #f5f5f5;
    }
    .header {
      background: linear-gradient(135deg, #2563EB, #3B82F6);
      color: white;
      padding: 30px;
      border-radius: 10px;
      margin-bottom: 30px;
    }
    .page {
      background: white;
      padding: 30px;
      margin-bottom: 20px;
      border-radius: 10px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .confidence {
      display: inline-block;
      padding: 5px 15px;
      border-radius: 20px;
      font-weight: bold;
      font-size: 14px;
    }
    .confidence-high { background-color: #10B981; color: white; }
    .confidence-medium { background-color: #2563EB; color: white; }
    .confidence-low { background-color: #EF4444; color: white; }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
    }
    th, td {
      border: 1px solid #ddd;
      padding: 12px;
      text-align: left;
    }
    th {
      background-color: #2563EB;
      color: white;
    }
    .page-number {
      color: #2563EB;
      font-weight: bold;
      font-size: 18px;
      margin-bottom: 15px;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>Strukturis - Documento Processado</h1>
    <p><strong>Arquivo:</strong> ${doc.originalFile.name}</p>
    <p><strong>Processado em:</strong> ${doc.processedAt.toLocaleString("pt-BR")}</p>
    <p><strong>Confiabilidade Geral:</strong> <span class="confidence confidence-${
      doc.overallConfidence >= 90 ? "high" : doc.overallConfidence >= 70 ? "medium" : "low"
    }">${doc.overallConfidence}%</span></p>
    <p><strong>Total de Páginas:</strong> ${doc.totalPages}</p>
  </div>
`;

  doc.pages.forEach((page) => {
    const confidenceClass =
      page.confidence >= 90 ? "high" : page.confidence >= 70 ? "medium" : "low";

    html += `
  <div class="page">
    <div class="page-number">Página ${page.pageNumber}</div>
    <p><strong>Confiabilidade:</strong> <span class="confidence confidence-${confidenceClass}">${page.confidence}%</span></p>
    <div style="white-space: pre-wrap; margin-top: 20px;">${page.text}</div>
`;

    if (page.hasTable && page.tableData && page.tableData.length > 0) {
      html += `
    <h3>Tabela Detectada</h3>
    <table>
      <thead>
        <tr>
          ${page.tableData[0].map((cell) => `<th>${cell}</th>`).join("")}
        </tr>
      </thead>
      <tbody>
        ${page.tableData
          .slice(1)
          .map(
            (row) => `
        <tr>
          ${row.map((cell) => `<td>${cell}</td>`).join("")}
        </tr>
        `
          )
          .join("")}
      </tbody>
    </table>
`;
    }

    html += `  </div>\n`;
  });

  html += `
</body>
</html>`;

  return new Blob([html], { type: "text/html;charset=utf-8" });
};

/**
 * Download blob as file
 */
export const downloadBlob = (blob: Blob, fileName: string) => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};
