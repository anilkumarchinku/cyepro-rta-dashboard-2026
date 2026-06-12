// Recommended Power Query cleanup if importing original Excel directly.
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
