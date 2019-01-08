import xlrd

if __name__ == '__main__':

    loc = ("Companies.xlsx")

    wb = xlrd.open_workbook(loc)
    sheet = wb.sheet_by_index(0)
    sheet.cell_value(0, 0)
    nRows = sheet.nrows
    print(sheet.cell_value(1,0))
    print(sheet.cell_value(1,3))

