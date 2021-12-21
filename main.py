import time
import datetime
import schedule
import db
import scrapers
from utilities import LOGGER


def run():
    START_DATE: datetime.date = datetime.date(2021, 1, 1)
    TODAY_DATE: datetime.date = datetime.date.today()
    gsheets_data = db.select_data_from_gsheets()
    db.today_to_csv(scrapers.today_scraper())

    if gsheets_data:
        
        while TODAY_DATE != gsheets_data[4]:
            data = scrapers.day_scraper(str(TODAY_DATE))
            if data:
                db.day_to_csv(data)
            TODAY_DATE -= datetime.timedelta(days=1)
        first_day_data = scrapers.day_scraper(str(TODAY_DATE))
        for i in range(len(first_day_data)):
            
            first_day_data[i].extend([None for i in range(15 - len(first_day_data[i]))])

            for j in gsheets_data[2][:gsheets_data[0]]:
                if first_day_data[i][8] == j[8] and len(j) >= 15:
                    first_day_data[i][14] = j[14]
                    first_day_data[i][15] = j[15]
                    break

        db.day_to_csv(first_day_data)
        db.day_to_csv(
            gsheets_data[2][gsheets_data[0] + 1:gsheets_data[1]], many=True)
        last_day = gsheets_data[3]
        while last_day != START_DATE:
            last_day -= datetime.timedelta(days=1)
            data = scrapers.day_scraper(str(last_day))
            if data:
                db.day_to_csv(data)

    else:
        while TODAY_DATE != START_DATE:

            data = scrapers.day_scraper(str(TODAY_DATE))

            if data:
                db.day_to_csv(data)

            TODAY_DATE -= datetime.timedelta(days=1)

    db.csv_to_gsheets()


# schedule.every().day.at("08:00").do(run)

# while True:
#     schedule.run_pending()
#     time.sleep(20)
run()