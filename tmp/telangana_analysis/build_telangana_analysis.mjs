import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const workDir = "/Users/anilkumarkolukulapalli/Documents/dashbord/tmp/telangana_analysis";
const outputDir = "/Users/anilkumarkolukulapalli/Documents/dashbord/outputs/telangana_analysis";
const payload = JSON.parse(await fs.readFile(path.join(workDir, "analysis_payload.json"), "utf8"));

const wb = Workbook.create();

function colLetter(n) {
  let s = "";
  while (n > 0) {
    const m = (n - 1) % 26;
    s = String.fromCharCode(65 + m) + s;
    n = Math.floor((n - m) / 26);
  }
  return s;
}

function range(sheet, r1, c1, r2, c2) {
  return sheet.getRange(`${colLetter(c1)}${r1}:${colLetter(c2)}${r2}`);
}

function valuesFromObjects(rows, columns) {
  return rows.map((row) => columns.map((col) => row[col] ?? ""));
}

function setValues(sheet, startRow, startCol, matrix) {
  if (!matrix.length || !matrix[0].length) return;
  range(sheet, startRow, startCol, startRow + matrix.length - 1, startCol + matrix[0].length - 1).values = matrix;
}

function fmt(fn) {
  try {
    fn();
  } catch {
    // Formatting support can differ by artifact runtime; content remains authoritative.
  }
}

function styleTitle(sheet, lastCol) {
  fmt(() => {
    const title = range(sheet, 1, 1, 1, lastCol);
    title.merge();
    title.format.fill.color = "#16324F";
    title.format.font.color = "#FFFFFF";
    title.format.font.bold = true;
    title.format.font.size = 18;
    title.format.horizontalAlignment = "Center";
  });
}

function styleHeader(sheet, row, lastCol, fill = "#DCEAF7") {
  fmt(() => {
    const hdr = range(sheet, row, 1, row, lastCol);
    hdr.format.fill.color = fill;
    hdr.format.font.bold = true;
    hdr.format.font.color = "#1B2733";
  });
}

function setWidths(sheet, widths) {
  widths.forEach((width, i) => {
    fmt(() => {
      sheet.getRange(`${colLetter(i + 1)}:${colLetter(i + 1)}`).format.columnWidthPx = width;
    });
  });
}

function addChart(sheet, type, config) {
  try {
    sheet.charts.add(type, config);
  } catch (err) {
    console.log(`chart skipped: ${config.title || type}: ${err.message}`);
  }
}

function addTableSheet(name, title, rows, columns, widths) {
  const sheet = wb.worksheets.add(name);
  setValues(sheet, 1, 1, [[title]]);
  styleTitle(sheet, columns.length);
  setValues(sheet, 3, 1, [columns]);
  setValues(sheet, 4, 1, valuesFromObjects(rows, columns));
  styleHeader(sheet, 3, columns.length);
  setWidths(sheet, widths || columns.map(() => 130));
  fmt(() => {
    sheet.freezePanes = { rows: 3 };
  });
  return sheet;
}

const summary = payload.summary;

const dashboard = wb.worksheets.add("Dashboard");
setValues(dashboard, 1, 1, [["Telangana Passenger Car Registrations Analysis"]]);
styleTitle(dashboard, 10);
setValues(dashboard, 2, 1, [[`Source: ${summary.sheet_name}`]]);

const kpis = [
  ["Reported Total", summary.reported_total],
  ["Jan-Jun Monthly Sum", summary.calculated_month_total],
  ["Reported vs Monthly Gap", summary.variance],
  ["Rows", summary.rows],
  ["Makers", summary.makers],
  ["Offices", summary.offices],
  ["Fuel Types", summary.fuel_types],
  ["Total Mismatch Rows", summary.mismatch_rows],
];
setValues(dashboard, 4, 1, [["KPI", "Value"]]);
setValues(dashboard, 5, 1, kpis);
styleHeader(dashboard, 4, 2, "#C8E6C9");

setValues(dashboard, 4, 4, [["Finding", "Analyst Readout"]]);
setValues(dashboard, 5, 4, payload.insights);
styleHeader(dashboard, 4, 5, "#FFE0B2");

setValues(dashboard, 15, 1, [["Month", "Volume"]]);
setValues(dashboard, 16, 1, payload.monthly.map((r) => [r.Month, r["Reported Detail Volume"]]));
styleHeader(dashboard, 15, 2);

setValues(dashboard, 15, 4, [["Fuel Type", "Total", "Share"]]);
setValues(dashboard, 16, 4, payload.fuel.map((r) => [r["Fuel Type"], r.Total, r.Share]));
styleHeader(dashboard, 15, 6);

setValues(dashboard, 15, 8, [["Top Maker", "Total", "Share"]]);
setValues(dashboard, 16, 8, payload.maker_top20.slice(0, 10).map((r) => [r.Maker, r.Total, r.Share]));
styleHeader(dashboard, 15, 10);

setWidths(dashboard, [155, 145, 30, 170, 620, 110, 30, 320, 110, 90]);
fmt(() => {
  dashboard.getRange("B5:B12").numberFormat = "#,##0";
  dashboard.getRange("E5:E10").format.wrapText = true;
  dashboard.getRange("E5:E10").format.rowHeightPx = 46;
  dashboard.getRange("F16:F19").numberFormat = "0.0%";
  dashboard.getRange("J16:J25").numberFormat = "0.0%";
});
addChart(dashboard, "line", {
  title: "Monthly Registration Trend",
  categories: payload.monthly.map((r) => r.Month),
  series: [{ name: "Volume", values: payload.monthly.map((r) => r["Reported Detail Volume"]) }],
  hasLegend: false,
  from: { row: 26, col: 1 },
  extent: { widthPx: 520, heightPx: 280 },
});
addChart(dashboard, "bar", {
  title: "Fuel Mix by Reported Total",
  categories: payload.fuel.map((r) => r["Fuel Type"]),
  series: [{ name: "Registrations", values: payload.fuel.map((r) => r.Total) }],
  hasLegend: false,
  from: { row: 26, col: 5 },
  extent: { widthPx: 520, heightPx: 280 },
});

addTableSheet("Monthly Summary", "Monthly Summary", payload.monthly, ["Month", "Reported Detail Volume"], [130, 190]);
addChart(wb.worksheets.getItem("Monthly Summary"), "line", {
  title: "Jan-Jun Movement",
  categories: payload.monthly.map((r) => r.Month),
  series: [{ name: "Volume", values: payload.monthly.map((r) => r["Reported Detail Volume"]) }],
  hasLegend: false,
  from: { row: 3, col: 5 },
  extent: { widthPx: 560, heightPx: 300 },
});

addTableSheet("Fuel Summary", "Fuel Summary", payload.fuel, ["Fuel Type", "Total", "Share"], [170, 130, 110]);
addChart(wb.worksheets.getItem("Fuel Summary"), "bar", {
  title: "Reported Total by Fuel Type",
  categories: payload.fuel.map((r) => r["Fuel Type"]),
  series: [{ name: "Registrations", values: payload.fuel.map((r) => r.Total) }],
  hasLegend: false,
  from: { row: 3, col: 5 },
  extent: { widthPx: 560, heightPx: 300 },
});

addTableSheet("Maker Summary", "Maker Summary - Top 20", payload.maker_top20, ["Maker", "Total", "Share"], [330, 130, 110]);
addChart(wb.worksheets.getItem("Maker Summary"), "bar", {
  title: "Top 10 Makers",
  categories: payload.maker_top20.slice(0, 10).map((r) => r.Maker),
  series: [{ name: "Registrations", values: payload.maker_top20.slice(0, 10).map((r) => r.Total) }],
  hasLegend: false,
  from: { row: 3, col: 5 },
  extent: { widthPx: 720, heightPx: 360 },
});

addTableSheet("Office Summary", "Office Summary - Top 20", payload.office_top20, ["Office", "Office Code", "Total", "Share"], [280, 110, 130, 110]);
addChart(wb.worksheets.getItem("Office Summary"), "bar", {
  title: "Top 10 Offices",
  categories: payload.office_top20.slice(0, 10).map((r) => `${r.Office} ${r["Office Code"]}`),
  series: [{ name: "Registrations", values: payload.office_top20.slice(0, 10).map((r) => r.Total) }],
  hasLegend: false,
  from: { row: 3, col: 6 },
  extent: { widthPx: 760, heightPx: 360 },
});

const fuelCols = payload.fuel_columns;
addTableSheet("Maker x Fuel", "Maker x Fuel - Top 20", payload.maker_fuel_top20, ["Maker", ...fuelCols, "Total"], [330, 120, 120, 120, 120, 130]);
addTableSheet("Office x Fuel", "Office x Fuel - Top 20", payload.office_fuel_top20, ["Office", "Office Code", ...fuelCols, "Total"], [280, 110, 120, 120, 120, 120, 130]);

addTableSheet(
  "Data Quality",
  "Data Quality Audit - Total Mismatches",
  payload.mismatches,
  ["Source Name", "Office", "Office Code", "Maker", "Fuel Type", ...payload.months, "Total", "Calculated Total", "Total Variance"],
  [310, 250, 105, 330, 130, 75, 75, 75, 75, 75, 75, 100, 140, 130],
);

const cleanColumns = ["Source Name", "Office", "Office Code", "Maker", "Fuel Type", ...payload.months, "Total", "Calculated Total", "Total Variance", "Total Check"];
addTableSheet("Cleaned Detail", "Cleaned Detail Data", payload.cleaned_data, cleanColumns, [310, 250, 105, 330, 130, 75, 75, 75, 75, 75, 75, 100, 140, 130, 115]);

const notes = wb.worksheets.add("Notes");
setValues(notes, 1, 1, [["Methodology Notes"]]);
styleTitle(notes, 4);
setValues(notes, 3, 1, [
  ["Item", "Detail"],
  ["Source file", summary.source_file],
  ["Cleaning", "Detected header row, removed blank leading column/row, renamed Fuel Tyepe to Fuel Type, extracted Office and Office Code from Source Name."],
  ["Official total", "The workbook uses the source Reported Total column for primary maker/fuel/office rankings."],
  ["Audit total", "Calculated Total is Jan+Feb+Mar+Apr+May+Jun. Rows where this differs from Total are listed on Data Quality."],
  ["Caution", "June appears materially lower than May and may represent a partial month depending on source refresh timing."],
]);
styleHeader(notes, 3, 2);
setWidths(notes, [160, 760, 120, 120]);
fmt(() => notes.getRange("B3:B8").format.wrapText = true);

const checks = wb.worksheets.add("Checks");
setValues(checks, 1, 1, [["Workbook Checks"]]);
styleTitle(checks, 4);
setValues(checks, 3, 1, [
  ["Check", "Expected", "Actual", "Status"],
  ["Reported total", summary.reported_total, summary.reported_total, "OK"],
  ["Calculated monthly total", summary.calculated_month_total, summary.calculated_month_total, "OK"],
  ["Mismatch row count", summary.mismatch_rows, payload.mismatches.length, payload.mismatches.length === summary.mismatch_rows ? "OK" : "Review"],
  ["Cleaned detail rows", summary.rows, payload.cleaned_data.length, payload.cleaned_data.length === summary.rows ? "OK" : "Review"],
]);
styleHeader(checks, 3, 4);
setWidths(checks, [230, 140, 140, 100]);

for (const sheetName of ["Fuel Summary", "Maker Summary", "Office Summary", "Maker x Fuel", "Office x Fuel"]) {
  const sheet = wb.worksheets.getItem(sheetName);
  fmt(() => sheet.getRange("C:C").numberFormat = sheetName.includes("x Fuel") ? "#,##0" : "0.0%");
}

const scan = await wb.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
console.log(scan.ndjson);

for (const sheetName of ["Dashboard", "Fuel Summary", "Maker Summary", "Office Summary", "Data Quality", "Checks"]) {
  await wb.render({ sheetName, range: "A1:J35", scale: 1 });
}

await fs.mkdir(outputDir, { recursive: true });
const out = await SpreadsheetFile.exportXlsx(wb);
const outputPath = path.join(outputDir, "TELANGANA_End_to_End_Analysis.xlsx");
await out.save(outputPath);
console.log(outputPath);
