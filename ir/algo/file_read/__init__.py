import xlrd
from mongoengine import *

from ir.algo.file_read.company_index import CompanyDailyIndex



if __name__ == '__main__':

    loc = ("../dataset/Companies.xlsx")
    connect('trading')

    wb = xlrd.open_workbook(loc)
    sheet = wb.sheet_by_index(0)

    for i in range(1, sheet.nrows):
        tx = CompanyDailyIndex(indicator=sheet.cell_value(i, 0), open_value=sheet.cell_value(i, 4),
                               high_value=sheet.cell_value(i, 5), low_value=sheet.cell_value(i, 6),
                               close_value=sheet.cell_value(i, 7), vol=sheet.cell_value(i, 8))
        tx.save()
