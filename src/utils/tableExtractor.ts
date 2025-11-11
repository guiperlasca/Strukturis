/**
 * Detect if text contains table-like structures
 */
export const detectTable = (text: string): boolean => {
  // Look for patterns that indicate tables:
  // - Multiple consecutive lines with similar structure
  // - Presence of delimiters (|, \t, multiple spaces)
  // - Numeric data patterns

  const lines = text.split("\n").filter((line) => line.trim().length > 0);

  if (lines.length < 3) return false;

  // Check for pipe delimiters
  const pipeCount = lines.filter((line) => line.includes("|")).length;
  if (pipeCount > lines.length * 0.5) return true;

  // Check for tab delimiters
  const tabCount = lines.filter((line) => line.includes("\t")).length;
  if (tabCount > lines.length * 0.5) return true;

  // Check for consistent spacing patterns
  const spacingPatterns = lines.map((line) => {
    const matches = line.match(/\s{2,}/g);
    return matches ? matches.length : 0;
  });

  const avgSpacing = spacingPatterns.reduce((a, b) => a + b, 0) / spacingPatterns.length;
  const consistentSpacing = spacingPatterns.filter((s) => Math.abs(s - avgSpacing) < 2).length;

  if (consistentSpacing > lines.length * 0.7 && avgSpacing > 2) return true;

  return false;
};

/**
 * Extract table data from text
 */
export const extractTableData = (text: string): string[][] => {
  const lines = text.split("\n").filter((line) => line.trim().length > 0);

  // Try pipe delimiter first
  if (lines[0].includes("|")) {
    return lines.map((line) =>
      line
        .split("|")
        .map((cell) => cell.trim())
        .filter((cell) => cell.length > 0)
    );
  }

  // Try tab delimiter
  if (lines[0].includes("\t")) {
    return lines.map((line) => line.split("\t").map((cell) => cell.trim()));
  }

  // Try multiple spaces
  return lines.map((line) =>
    line
      .split(/\s{2,}/)
      .map((cell) => cell.trim())
      .filter((cell) => cell.length > 0)
  );
};

/**
 * Format table data as markdown
 */
export const formatTableAsMarkdown = (tableData: string[][]): string => {
  if (tableData.length === 0) return "";

  const maxColumns = Math.max(...tableData.map((row) => row.length));

  // Header
  let markdown = "| " + tableData[0].join(" | ") + " |\n";

  // Separator
  markdown += "| " + Array(maxColumns).fill("---").join(" | ") + " |\n";

  // Rows
  for (let i = 1; i < tableData.length; i++) {
    markdown += "| " + tableData[i].join(" | ") + " |\n";
  }

  return markdown;
};
