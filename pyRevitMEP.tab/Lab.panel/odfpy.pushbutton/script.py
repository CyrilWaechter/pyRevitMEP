# coding: utf8
import odf
from odf.table import TableRow, TableCell, Table
from odf.opendocument import OpenDocumentSpreadsheet, load
from odf.text import P

# Create a new ods file
ods_doc = OpenDocumentSpreadsheet()
# Create a new Table/Sheet
sheet = Table(name="odfpy_ods")
# Create a new empty row
tablerow = TableRow()
# Create 3 new cells with different value type
cell1 = TableCell(valuetype="string")
cell1.addElement(P(text="Hello World !"))
cell2 = TableCell(valuetype="float", value=1)
cell3 = TableCell(valuetype="currency", currency="CHF", value="-8100")
# Add these cells to the row
tablerow.addElement(cell1)
tablerow.addElement(cell2)
tablerow.addElement(cell3)
# Add the row to the table
sheet.addElement(tablerow)
# Add the table/sheet to the ods document
ods_doc.spreadsheet.addElement(sheet)
# Save the document
ods_doc.save(r"C:\FichiersLocauxRevit\odfpy.ods")


# Load an ods document
ods_doc = load(r"C:\FichiersLocauxRevit\odfpy.ods")
# Get first sheet
sheet = ods_doc.getElementsByType(Table)[0]
# Get cell a i, j (row, column)
i, j = 1, 2
row = sheet.getElementsByType(TableRow)[i-1]
cell = row.getElementsByType(TableCell)[j-1]
print cell.value
