# Telangana Power BI Dashboard Build Guide

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
- Reported Total: 76,353
- Calculated Monthly Total: 103,211
- Variance: -26,858
- Makers: 41
- Offices: 67
- Mismatch Rows: 22

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
