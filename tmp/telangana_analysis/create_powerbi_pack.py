import csv
import json
from pathlib import Path

base = Path("/Users/anilkumarkolukulapalli/Documents/dashbord")
payload_path = base / "tmp/telangana_analysis/analysis_payload.json"
out = base / "outputs/telangana_analysis/PowerBI_Build_Pack"
out.mkdir(parents=True, exist_ok=True)

payload = json.loads(payload_path.read_text(encoding="utf-8"))
months = payload["months"]
month_no = {m: i + 1 for i, m in enumerate(months)}

wide = payload["cleaned_data"]
wide_columns = [
    "Source Name",
    "Office",
    "Office Code",
    "Maker",
    "Fuel Type",
    *months,
    "Total",
    "Calculated Total",
    "Total Variance",
    "Total Check",
]

with (out / "TELANGANA_PowerBI_Wide.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=wide_columns)
    writer.writeheader()
    writer.writerows(wide)

monthly_rows = []
for row in wide:
    for month in months:
        monthly_rows.append(
            {
                "Source Name": row["Source Name"],
                "Office": row["Office"],
                "Office Code": row["Office Code"],
                "Maker": row["Maker"],
                "Fuel Type": row["Fuel Type"],
                "Month": month,
                "Month No": month_no[month],
                "Month Date": f"2026-{month_no[month]:02d}-01",
                "Registrations": row[month],
                "Reported Total": row["Total"],
                "Calculated Total": row["Calculated Total"],
                "Total Variance": row["Total Variance"],
                "Total Check": row["Total Check"],
            }
        )

monthly_columns = [
    "Source Name",
    "Office",
    "Office Code",
    "Maker",
    "Fuel Type",
    "Month",
    "Month No",
    "Month Date",
    "Registrations",
    "Reported Total",
    "Calculated Total",
    "Total Variance",
    "Total Check",
]

with (out / "TELANGANA_PowerBI_Monthly.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=monthly_columns)
    writer.writeheader()
    writer.writerows(monthly_rows)

with (out / "Month_Dim.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Month", "Month No", "Month Date", "Month Label"])
    writer.writeheader()
    for month in months:
        writer.writerow(
            {
                "Month": month,
                "Month No": month_no[month],
                "Month Date": f"2026-{month_no[month]:02d}-01",
                "Month Label": f"{month} 2026",
            }
        )

def write_dim(name, fieldnames, rows):
    with (out / name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

write_dim(
    "Maker_Dim.csv",
    ["Maker"],
    [{"Maker": value} for value in sorted({row["Maker"] for row in wide})],
)
write_dim(
    "Fuel_Type_Dim.csv",
    ["Fuel Type"],
    [{"Fuel Type": value} for value in sorted({row["Fuel Type"] for row in wide})],
)
office_seen = {}
for row in wide:
    office_seen[(row["Office"], row["Office Code"])] = {
        "Office": row["Office"],
        "Office Code": row["Office Code"],
    }
write_dim(
    "Office_Dim.csv",
    ["Office", "Office Code"],
    sorted(office_seen.values(), key=lambda r: (r["Office"], r["Office Code"])),
)

theme = {
    "name": "Telangana Executive Navy",
    "dataColors": ["#2F80ED", "#27AE60", "#F2C94C", "#9B51E0", "#56CCF2", "#F2994A"],
    "background": "#F7F9FC",
    "foreground": "#16324F",
    "tableAccent": "#2F80ED",
    "visualStyles": {
        "*": {
            "*": {
                "title": [
                    {
                        "show": True,
                        "fontColor": {"solid": {"color": "#16324F"}},
                        "fontSize": 12,
                        "fontFamily": "Segoe UI Semibold",
                    }
                ],
                "background": [{"show": True, "color": {"solid": {"color": "#FFFFFF"}}, "transparency": 0}],
                "border": [{"show": False}],
            }
        },
        "card": {
            "*": {
                "labels": [{"color": {"solid": {"color": "#16324F"}}, "fontSize": 22, "fontFamily": "Segoe UI Semibold"}],
                "categoryLabels": [{"color": {"solid": {"color": "#6B7280"}}, "fontSize": 10}],
            }
        },
    },
}
(out / "Telangana_PowerBI_Theme.json").write_text(json.dumps(theme, indent=2), encoding="utf-8")

dax = """-- Table names assumed:
--   TELANGANA_PowerBI_Wide
--   TELANGANA_PowerBI_Monthly
--   Month_Dim

Total Registrations =
SUM('TELANGANA_PowerBI_Wide'[Total])

Calculated Monthly Total =
SUM('TELANGANA_PowerBI_Wide'[Calculated Total])

Total Variance =
[Total Registrations] - [Calculated Monthly Total]

Variance Alert =
IF([Total Variance] < 0, "Review source totals", "OK")

Maker Count =
DISTINCTCOUNT('TELANGANA_PowerBI_Wide'[Maker])

Office Count =
DISTINCTCOUNT('TELANGANA_PowerBI_Wide'[Office])

Fuel Type Count =
DISTINCTCOUNT('TELANGANA_PowerBI_Wide'[Fuel Type])

Mismatch Row Count =
COUNTROWS(
    FILTER(
        'TELANGANA_PowerBI_Wide',
        'TELANGANA_PowerBI_Wide'[Total Check] = "Mismatch"
    )
)

Registration Share =
DIVIDE(
    [Total Registrations],
    CALCULATE([Total Registrations], ALL('TELANGANA_PowerBI_Wide'))
)

Monthly Registrations =
SUM('TELANGANA_PowerBI_Monthly'[Registrations])

Previous Month Registrations =
CALCULATE(
    [Monthly Registrations],
    FILTER(
        ALL('Month_Dim'),
        'Month_Dim'[Month No] = MAX('Month_Dim'[Month No]) - 1
    )
)

MoM Change =
[Monthly Registrations] - [Previous Month Registrations]

MoM Change % =
DIVIDE([MoM Change], [Previous Month Registrations])

May Registrations =
CALCULATE(
    [Monthly Registrations],
    'Month_Dim'[Month] = "May"
)

June Registrations =
CALCULATE(
    [Monthly Registrations],
    'Month_Dim'[Month] = "Jun"
)

May to June Change =
[June Registrations] - [May Registrations]

May to June Change % =
DIVIDE([May to June Change], [May Registrations])

Top Maker Label =
VAR TopMaker =
    TOPN(
        1,
    SUMMARIZE(
            'Maker_Dim',
            'Maker_Dim'[Maker],
            "MakerTotal", [Total Registrations]
        ),
        [MakerTotal], DESC
    )
RETURN
CONCATENATEX(TopMaker, 'Maker_Dim'[Maker])

Top Office Label =
VAR TopOffice =
    TOPN(
        1,
    SUMMARIZE(
            'Office_Dim',
            'Office_Dim'[Office],
            "OfficeTotal", [Total Registrations]
        ),
        [OfficeTotal], DESC
    )
RETURN
CONCATENATEX(TopOffice, 'Office_Dim'[Office])
"""
(out / "PowerBI_DAX_Measures.dax").write_text(dax, encoding="utf-8")

power_query = """// Recommended Power Query cleanup if importing original Excel directly.
// Easier path: import the prepared CSV files in this folder.

let
    Source = Excel.Workbook(File.Contents("TELANGANA.xlsx"), null, true),
    Sheet = Source{[Item="VAHAN ALL FUELS CARS 09TH JUN 2",Kind="Sheet"]}[Data],
    RemovedBlankRows = Table.SelectRows(Sheet, each List.NonNullCount(Record.FieldValues(_)) > 0),
    PromotedHeaders = Table.PromoteHeaders(RemovedBlankRows, [PromoteAllScalars=true]),
    RemovedBlankColumns = Table.RemoveColumns(PromotedHeaders, {"Column1"}),
    RenamedColumns = Table.RenameColumns(RemovedBlankColumns, {{"Source.Name", "Source Name"}, {"Fuel Tyepe", "Fuel Type"}}),
    TrimmedText = Table.TransformColumns(
        RenamedColumns,
        {
            {"Source Name", Text.Trim, type text},
            {"Maker", Text.Trim, type text},
            {"Fuel Type", Text.Trim, type text}
        }
    ),
    ChangedTypes = Table.TransformColumnTypes(
        TrimmedText,
        {
            {"Jan", Int64.Type}, {"Feb", Int64.Type}, {"Mar", Int64.Type},
            {"Apr", Int64.Type}, {"May", Int64.Type}, {"Jun", Int64.Type},
            {"Total", Int64.Type}
        }
    ),
    AddedCalculatedTotal = Table.AddColumn(ChangedTypes, "Calculated Total", each [Jan] + [Feb] + [Mar] + [Apr] + [May] + [Jun], Int64.Type),
    AddedVariance = Table.AddColumn(AddedCalculatedTotal, "Total Variance", each [Total] - [Calculated Total], Int64.Type),
    AddedCheck = Table.AddColumn(AddedVariance, "Total Check", each if [Total Variance] = 0 then "OK" else "Mismatch", type text)
in
    AddedCheck
"""
(out / "PowerQuery_Cleanup_Template.pq").write_text(power_query, encoding="utf-8")

layout = f"""# Telangana Power BI Dashboard Build Guide

## Final Dashboard Title
Telangana Car Registrations Dashboard | Jan-Jun 2026

## Main Goal
Create a single-screen executive dashboard that lets managers understand registrations, maker leadership, fuel mix, office concentration, monthly trend, and source-data quality at a glance.

## Business Questions
- What is the reported registration volume?
- Which makers and fuel types dominate?
- Which RTA offices contribute the most?
- How did Jan-Jun registrations move month by month?
- Where does the source data need review?

## Page Names
1. Executive Overview
2. Data Quality Audit, optional drill page

## Data Model
Import these CSV files:
- TELANGANA_PowerBI_Wide.csv
- TELANGANA_PowerBI_Monthly.csv
- Month_Dim.csv
- Maker_Dim.csv
- Fuel_Type_Dim.csv
- Office_Dim.csv

Create relationships:
- Month_Dim[Month No] one-to-many to TELANGANA_PowerBI_Monthly[Month No]
- Maker_Dim[Maker] one-to-many to TELANGANA_PowerBI_Wide[Maker]
- Maker_Dim[Maker] one-to-many to TELANGANA_PowerBI_Monthly[Maker]
- Fuel_Type_Dim[Fuel Type] one-to-many to TELANGANA_PowerBI_Wide[Fuel Type]
- Fuel_Type_Dim[Fuel Type] one-to-many to TELANGANA_PowerBI_Monthly[Fuel Type]
- Office_Dim[Office] one-to-many to TELANGANA_PowerBI_Wide[Office]
- Office_Dim[Office] one-to-many to TELANGANA_PowerBI_Monthly[Office]

Sort:
- Sort Month_Dim[Month] by Month_Dim[Month No]
- Sort Month_Dim[Month Label] by Month_Dim[Month No]

## 16:9 Single-Screen Layout
Canvas: 1280 x 720, background #F7F9FC.

Top title band:
- X 24, Y 16, W 1232, H 44
- Title text: Telangana Car Registrations Dashboard | Jan-Jun 2026
- Subtitle: VAHAN Telangana all-fuels passenger car registrations

Left slicer rail:
- X 24, Y 76, W 190, H 608
- Slicers: Fuel_Type_Dim[Fuel Type], Maker_Dim[Maker], Office_Dim[Office], Office_Dim[Office Code]

KPI cards:
- X 230, Y 76, W 195, H 86: Total Registrations
- X 439, Y 76, W 195, H 86: Calculated Monthly Total
- X 648, Y 76, W 195, H 86: Total Variance
- X 857, Y 76, W 185, H 86: Maker Count
- X 1056, Y 76, W 200, H 86: Mismatch Row Count

Middle visuals:
- X 230, Y 178, W 510, H 230: Monthly Registration Trend
- X 756, Y 178, W 245, H 230: Fuel Mix
- X 1016, Y 178, W 240, H 230: Top Offices

Lower visuals:
- X 230, Y 424, W 510, H 260: Top 10 Makers
- X 756, Y 424, W 500, H 260: Detail Matrix

## Visual List

### KPI Card: Total Registrations
Fields: [Total Registrations]
Insight: Reported total from the source Total column.
Use: The primary number managers will ask for first.

### KPI Card: Calculated Monthly Total
Fields: [Calculated Monthly Total]
Insight: Sum of Jan-Jun monthly values.
Use: Makes source reconciliation visible.

### KPI Card: Total Variance
Fields: [Total Variance]
Insight: Difference between reported source total and monthly sum.
Use: Should be red because current variance is negative.

### KPI Card: Mismatch Row Count
Fields: [Mismatch Row Count]
Insight: Number of rows where Total does not equal Jan-Jun sum.
Use: Direct data-quality warning.

### Line Chart: Monthly Registration Trend
Axis: Month_Dim[Month Label]
Values: [Monthly Registrations]
Insight: January is high, June is much lower than May.
Use: Trend is understood immediately.

### Bar Chart: Top 10 Makers
Axis: Maker_Dim[Maker]
Values: [Total Registrations]
Filter: Top N = 10 by [Total Registrations]
Insight: Shows market leaders.
Use: Strongest comparison visual.

### Donut Chart: Fuel Mix
Legend: Fuel_Type_Dim[Fuel Type]
Values: [Total Registrations]
Insight: Petrol and Petrol CNG dominate.
Use: Share-of-whole is useful because there are only 4 fuel categories.

### Bar Chart: Top Offices
Axis: Office_Dim[Office]
Values: [Total Registrations]
Filter: Top N = 8 by [Total Registrations]
Insight: Shows office concentration.
Use: Keeps regional operations visible.

### Matrix: Maker x Fuel Detail
Rows: Maker_Dim[Maker]
Columns: Fuel_Type_Dim[Fuel Type]
Values: [Total Registrations], [Calculated Monthly Total], [Total Variance]
Insight: Detailed drilldown by maker and fuel.
Use: Supports follow-up after reading the charts.

## Design Style
- Background: #F7F9FC
- Cards/visual containers: #FFFFFF
- Primary text: #16324F
- Accent: #2F80ED
- Positive: #27AE60
- Negative: #EB5757
- Font: Segoe UI
- Use rounded visual containers, subtle shadow, and 12-16 px spacing.

## Current Numbers To Validate
- Reported Total: {payload["summary"]["reported_total"]:,}
- Calculated Monthly Total: {payload["summary"]["calculated_month_total"]:,}
- Variance: {payload["summary"]["variance"]:,}
- Makers: {payload["summary"]["makers"]:,}
- Offices: {payload["summary"]["offices"]:,}
- Mismatch Rows: {payload["summary"]["mismatch_rows"]:,}

## Build Steps
1. Open Power BI Desktop.
2. Get Data > Text/CSV and import all six CSV files from this folder.
3. Set numeric columns to Whole Number.
4. Set Month Date to Date.
5. Create the relationships listed in the Data Model section.
6. Sort Month and Month Label by Month No.
7. Use dimension fields for slicers and chart axes so all visuals filter together.
8. Import Telangana_PowerBI_Theme.json from View > Themes > Browse for themes.
9. Create the measures from PowerBI_DAX_Measures.dax.
10. Build the Executive Overview page using the coordinates above.
11. Add conditional formatting: Total Variance red when below 0, green when 0 or above.
12. Keep all charts sorted descending except the monthly line chart.
13. Publish or export once the KPI cards match the validation numbers above.

## Premium Finish Tips
- Hide gridlines and unnecessary visual headers.
- Keep slicers compact with search enabled.
- Use Top N filters so the page does not feel crowded.
- Put the red variance card near the top so data-quality risk is impossible to miss.
- Use tooltips for Calculated Total, Variance, Office Code, and Source Name.
"""
(out / "PowerBI_Dashboard_Build_Guide.md").write_text(layout, encoding="utf-8")

html = """<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>Telangana Power BI Dashboard Mockup</title>
<style>
  body { margin:0; background:#dfe7f1; font-family: Segoe UI, Arial, sans-serif; color:#16324F; }
  .canvas { width:1280px; height:720px; margin:24px auto; background:#F7F9FC; position:relative; box-shadow:0 20px 60px rgba(22,50,79,.18); overflow:hidden; }
  .title { position:absolute; left:24px; top:14px; right:24px; height:48px; }
  h1 { margin:0; font-size:24px; line-height:30px; }
  .subtitle { color:#6B7280; font-size:12px; }
  .rail { position:absolute; left:24px; top:76px; width:190px; height:608px; background:#fff; border-radius:16px; box-shadow:0 8px 24px rgba(22,50,79,.08); padding:16px; box-sizing:border-box; }
  .rail h3 { margin:0 0 14px; font-size:13px; }
  .slicer { height:48px; border:1px solid #D9E2EF; border-radius:10px; margin-bottom:12px; padding:8px 10px; box-sizing:border-box; color:#6B7280; font-size:12px; background:#FBFCFE; }
  .card, .visual { position:absolute; background:#fff; border-radius:16px; box-shadow:0 8px 24px rgba(22,50,79,.08); box-sizing:border-box; padding:14px 16px; }
  .card .label { color:#6B7280; font-size:12px; }
  .card .num { font-size:28px; font-weight:700; margin-top:8px; }
  .neg { color:#EB5757; }
  .visual h2 { font-size:14px; margin:0 0 12px; }
  .bar { height:16px; background:#E8F1FE; border-radius:9px; margin:11px 0; overflow:hidden; }
  .fill { height:100%; background:#2F80ED; border-radius:9px; }
  .line { height:150px; border-left:1px solid #D9E2EF; border-bottom:1px solid #D9E2EF; position:relative; }
  .line svg { position:absolute; inset:0; }
  .donut { width:120px; height:120px; border-radius:50%; background:conic-gradient(#2F80ED 0 51%, #27AE60 51% 80.7%, #F2C94C 80.7% 99.8%, #9B51E0 99.8%); margin:18px auto 8px; position:relative; }
  .donut:after { content:""; position:absolute; inset:28px; background:white; border-radius:50%; }
  table { width:100%; border-collapse:collapse; font-size:11px; }
  th { text-align:left; color:#6B7280; border-bottom:1px solid #D9E2EF; padding:6px; }
  td { border-bottom:1px solid #EEF3F8; padding:6px; }
</style>
</head>
<body>
<div class="canvas">
  <div class="title"><h1>Telangana Car Registrations Dashboard | Jan-Jun 2026</h1><div class="subtitle">VAHAN Telangana all-fuels passenger car registrations</div></div>
  <div class="rail"><h3>Filters</h3><div class="slicer">Fuel Type</div><div class="slicer">Maker</div><div class="slicer">Office</div><div class="slicer">Office Code</div></div>
  <div class="card" style="left:230px;top:76px;width:195px;height:86px"><div class="label">Total Registrations</div><div class="num">76,353</div></div>
  <div class="card" style="left:439px;top:76px;width:195px;height:86px"><div class="label">Monthly Sum</div><div class="num">103,211</div></div>
  <div class="card" style="left:648px;top:76px;width:195px;height:86px"><div class="label">Total Variance</div><div class="num neg">-26,858</div></div>
  <div class="card" style="left:857px;top:76px;width:185px;height:86px"><div class="label">Makers</div><div class="num">41</div></div>
  <div class="card" style="left:1056px;top:76px;width:200px;height:86px"><div class="label">Mismatch Rows</div><div class="num neg">22</div></div>
  <div class="visual" style="left:230px;top:178px;width:510px;height:230px"><h2>Monthly Registration Trend</h2><div class="line"><svg viewBox="0 0 460 150"><polyline fill="none" stroke="#2F80ED" stroke-width="4" points="10,28 98,76 186,72 274,98 362,52 450,130"/></svg></div></div>
  <div class="visual" style="left:756px;top:178px;width:245px;height:230px"><h2>Fuel Mix</h2><div class="donut"></div><div style="font-size:12px;color:#6B7280;text-align:center">Petrol leads at 50.9%</div></div>
  <div class="visual" style="left:1016px;top:178px;width:240px;height:230px"><h2>Top Offices</h2><div class="bar"><div class="fill" style="width:100%"></div></div><div class="bar"><div class="fill" style="width:66%"></div></div><div class="bar"><div class="fill" style="width:55%"></div></div><div class="bar"><div class="fill" style="width:51%"></div></div><div class="bar"><div class="fill" style="width:50%"></div></div></div>
  <div class="visual" style="left:230px;top:424px;width:510px;height:260px"><h2>Top 10 Makers</h2><div class="bar"><div class="fill" style="width:100%"></div></div><div class="bar"><div class="fill" style="width:72%"></div></div><div class="bar"><div class="fill" style="width:53%"></div></div><div class="bar"><div class="fill" style="width:43%"></div></div><div class="bar"><div class="fill" style="width:33%"></div></div></div>
  <div class="visual" style="left:756px;top:424px;width:500px;height:260px"><h2>Maker x Fuel Detail</h2><table><tr><th>Maker</th><th>Petrol</th><th>CNG</th><th>Diesel</th><th>Total</th></tr><tr><td>Maruti Suzuki</td><td>9,545</td><td>7,850</td><td>0</td><td>17,395</td></tr><tr><td>Tata Motors</td><td>7,502</td><td>3,908</td><td>1,166</td><td>12,576</td></tr><tr><td>Hyundai</td><td>5,871</td><td>1,708</td><td>1,689</td><td>9,268</td></tr></table></div>
</div>
</body>
</html>
"""
(out / "Dashboard_Single_Screen_Mockup.html").write_text(html, encoding="utf-8")

print(out)
