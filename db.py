import csv
import datetime

from openpyxl import Workbook
from settings import GENERAL_XLSX_COLUMNS
import pygsheets
from time import sleep
from utilities import LOGGER


def select_data_from_gsheets() -> tuple:

    gc = pygsheets.authorize()

    sh = gc.open('TimeForm')
    wks = sh.sheet1

    date = wks.get_value("A2")
    if date:
        data = wks.get_col(col=1, include_tailing_empty=False)
        all_data = wks.get_all_values(include_tailing_empty=False, include_tailing_empty_rows=False)
        wks.sort_range(start='A1', end='V'+str(len(all_data)), basecolumnindex=0, sortorder='DESCENDING')
        first_day = [int(i) for i in all_data[-1][0].split("/")[::-1]]
        first_day[0] += 2000
        first_day = datetime.date(*first_day)
        last_day = [int(i) for i in date.split("/")[::-1]]
        last_day[0] += 2000
        last_day = datetime.date(*last_day)
        today_races = data.count(date)

        another_races = len(data) - 1


        return (today_races, another_races, all_data, first_day, last_day)
    else: return None


#####################################################
######################  CSV  ########################
#####################################################

def today_to_csv(data):
    with open("TempData.csv", mode="w", encoding='utf-8') as w_file:
        file_writer = csv.writer(w_file, delimiter = ",", lineterminator="\r")
        file_writer.writerow(GENERAL_XLSX_COLUMNS)
        data.sort(key=lambda x:x[1],reverse=False)

        for header in data:
            header = header
            file_writer.writerow(header)


def day_to_csv(data, many=False):
    
    with open("TempData.csv", mode="a", encoding='utf-8') as a_file:

        file_writer = csv.writer(a_file, delimiter = ",", lineterminator="\r")

        if many:
            for header in data: file_writer.writerow(header)
        else: 
            data.sort(key=lambda x:x[1],reverse=False)
            file_writer.writerows(data)


#####################################################
################# CSV TO GSHEETS ####################
#####################################################


def csv_to_gsheets():
    try:
        gc = pygsheets.authorize()

        sh = gc.open('TimeForm')
        wks = sh.sheet1
        wks.clear()
        all_rows = len(wks.get_all_values(include_tailing_empty=True, include_tailing_empty_rows=True))
        if all_rows: all_rows -= 1
        with open('TempData.csv') as f:
            reader = csv.reader(f, delimiter=',')
            csv_data = [row for row in reader]
            amount_of_rows = len(csv_data)
            wks.delete_rows(index=1, number=all_rows)
            wks.insert_rows(0, number=amount_of_rows, values=csv_data)
    except:
        LOGGER.info(
                "Error with connect to GSheets"
            )
        sleep(250)


# if __name__ == '__main__':
#     csv_to_gsheets()