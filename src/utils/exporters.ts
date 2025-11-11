import { ProcessedDocument, PageResult } from "@/types/document";
import * as XLSX from "xlsx";
import { Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableCell, TableRow } from "docx";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

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
 * Export to Excel (.xlsx)
 */
export const exportToExcel = (doc: ProcessedDocument): Blob => {
  const workbook = XLSX.utils.book_new();

  // Summary sheet
  const summaryData = [
    ["Strukturis - Relatório de Processamento OCR"],
    [],
    ["Arquivo:", doc.originalFile.name],
    ["Processado em:", doc.processedAt.toLocaleString("pt-BR")],
    ["Confiabilidade Geral:", `${doc.overallConfidence}%`],
    ["Total de Páginas:", doc.totalPages],
    ["Tipo de Documento:", doc.documentType?.label || "Não identificado"],
    ["Idioma:", doc.detectedLanguage || "pt-BR"],
    ["Tempo de Processamento:", `${(doc.processingTime / 1000).toFixed(2)}s`],
    [],
    ["Página", "Confiabilidade", "Tem Tabela", "Caracteres"],
  ];

  doc.pages.forEach((page) => {
    summaryData.push([
      page.pageNumber,
      `${page.confidence}%`,
      page.hasTable ? "Sim" : "Não",
      page.text.length,
    ]);
  });

  const summarySheet = XLSX.utils.aoa_to_sheet(summaryData);
  XLSX.utils.book_append_sheet(workbook, summarySheet, "Resumo");

  // Text pages
  doc.pages.forEach((page) => {
    const pageData = [
      [`Página ${page.pageNumber}`],
      [`Confiabilidade: ${page.confidence}%`],
      [],
      [page.text],
    ];

    const pageSheet = XLSX.utils.aoa_to_sheet(pageData);
    const sheetName = `Página ${page.pageNumber}`.substring(0, 31);
    XLSX.utils.book_append_sheet(workbook, pageSheet, sheetName);
  });

  // Tables sheet (if any)
  const tablesData: any[] = [["Strukturis - Tabelas Extraídas"], []];
  let hasAnyTable = false;

  doc.pages.forEach((page) => {
    if (page.hasTable && page.tableData && page.tableData.length > 0) {
      hasAnyTable = true;
      tablesData.push([`Página ${page.pageNumber}`]);
      page.tableData.forEach((row) => {
        tablesData.push(row);
      });
      tablesData.push([]);
    }
  });

  if (hasAnyTable) {
    const tablesSheet = XLSX.utils.aoa_to_sheet(tablesData);
    XLSX.utils.book_append_sheet(workbook, tablesSheet, "Tabelas");
  }

  const excelBuffer = XLSX.write(workbook, { type: "array", bookType: "xlsx" });
  return new Blob([excelBuffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
};

/**
 * Export to Word (.docx)
 */
export const exportToWord = async (doc: ProcessedDocument): Promise<Blob> => {
  const children: any[] = [];

  // Header
  children.push(
    new Paragraph({
      text: "Strukturis - Documento Processado",
      heading: HeadingLevel.HEADING_1,
      spacing: { after: 200 },
    })
  );

  children.push(
    new Paragraph({
      children: [
        new TextRun({ text: "Arquivo: ", bold: true }),
        new TextRun(doc.originalFile.name),
      ],
      spacing: { after: 100 },
    })
  );

  children.push(
    new Paragraph({
      children: [
        new TextRun({ text: "Processado em: ", bold: true }),
        new TextRun(doc.processedAt.toLocaleString("pt-BR")),
      ],
      spacing: { after: 100 },
    })
  );

  children.push(
    new Paragraph({
      children: [
        new TextRun({ text: "Confiabilidade Geral: ", bold: true }),
        new TextRun(`${doc.overallConfidence}%`),
      ],
      spacing: { after: 100 },
    })
  );

  children.push(
    new Paragraph({
      children: [
        new TextRun({ text: "Total de Páginas: ", bold: true }),
        new TextRun(String(doc.totalPages)),
      ],
      spacing: { after: 300 },
    })
  );

  // Pages
  doc.pages.forEach((page, index) => {
    if (index > 0) {
      children.push(
        new Paragraph({
          text: "",
          pageBreakBefore: true,
        })
      );
    }

    children.push(
      new Paragraph({
        text: `Página ${page.pageNumber}`,
        heading: HeadingLevel.HEADING_2,
        spacing: { after: 200 },
      })
    );

    children.push(
      new Paragraph({
        children: [
          new TextRun({ text: "Confiabilidade: ", bold: true }),
          new TextRun(`${page.confidence}%`),
        ],
        spacing: { after: 200 },
      })
    );

    // Split text into paragraphs
    const textParagraphs = page.text.split("\n").filter((line) => line.trim());
    textParagraphs.forEach((line) => {
      children.push(
        new Paragraph({
          text: line,
          spacing: { after: 100 },
        })
      );
    });

    // Add table if exists
    if (page.hasTable && page.tableData && page.tableData.length > 0) {
      children.push(
        new Paragraph({
          text: "Tabela Detectada",
          heading: HeadingLevel.HEADING_3,
          spacing: { before: 200, after: 100 },
        })
      );

      const tableRows = page.tableData.map(
        (row) =>
          new TableRow({
            children: row.map(
              (cell) =>
                new TableCell({
                  children: [new Paragraph(cell)],
                })
            ),
          })
      );

      children.push(
        new Table({
          rows: tableRows,
        })
      );
    }
  });

  const docx = new Document({
    sections: [
      {
        children,
      },
    ],
  });

  const buffer = await Packer.toBlob(docx);
  return buffer;
};

/**
 * Export to searchable PDF
 */
export const exportToPDF = (doc: ProcessedDocument): Blob => {
  const pdf = new jsPDF();
  let yPosition = 20;

  // Header
  pdf.setFontSize(18);
  pdf.setFont("helvetica", "bold");
  pdf.text("Strukturis - Documento Processado", 20, yPosition);
  yPosition += 10;

  pdf.setFontSize(10);
  pdf.setFont("helvetica", "normal");
  pdf.text(`Arquivo: ${doc.originalFile.name}`, 20, yPosition);
  yPosition += 6;
  pdf.text(`Processado em: ${doc.processedAt.toLocaleString("pt-BR")}`, 20, yPosition);
  yPosition += 6;
  pdf.text(`Confiabilidade Geral: ${doc.overallConfidence}%`, 20, yPosition);
  yPosition += 6;
  pdf.text(`Total de Páginas: ${doc.totalPages}`, 20, yPosition);
  yPosition += 15;

  // Pages
  doc.pages.forEach((page, index) => {
    if (index > 0) {
      pdf.addPage();
      yPosition = 20;
    }

    pdf.setFontSize(14);
    pdf.setFont("helvetica", "bold");
    pdf.text(`Página ${page.pageNumber}`, 20, yPosition);
    yPosition += 8;

    pdf.setFontSize(10);
    pdf.setFont("helvetica", "normal");
    pdf.text(`Confiabilidade: ${page.confidence}%`, 20, yPosition);
    yPosition += 10;

    // Add text with word wrap
    const textLines = pdf.splitTextToSize(page.text, 170);
    textLines.forEach((line: string) => {
      if (yPosition > 270) {
        pdf.addPage();
        yPosition = 20;
      }
      pdf.text(line, 20, yPosition);
      yPosition += 6;
    });

    // Add table if exists
    if (page.hasTable && page.tableData && page.tableData.length > 0) {
      yPosition += 5;
      if (yPosition > 200) {
        pdf.addPage();
        yPosition = 20;
      }

      pdf.setFontSize(12);
      pdf.setFont("helvetica", "bold");
      pdf.text("Tabela Detectada", 20, yPosition);
      yPosition += 5;

      autoTable(pdf, {
        startY: yPosition,
        head: [page.tableData[0]],
        body: page.tableData.slice(1),
        theme: "grid",
        styles: { fontSize: 8 },
        headStyles: { fillColor: [37, 99, 235] },
      });

      yPosition = (pdf as any).lastAutoTable.finalY + 10;
    }
  });

  return pdf.output("blob");
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
