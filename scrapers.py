import time
import datetime as dt

from bs4 import BeautifulSoup as BS
from browser import get_cookies

from settings import HOME_URL
from utilities import get_race_type_name, LOGGER, get_html_page


COOKIES = get_cookies()


class RaceScraper:
    def __init__(self) -> None:
        self.race_data = []
        self.date_and_time = {}

    def get_race_venues(self, html, today=False) -> list:
        race_links = []

        if not html:
            LOGGER.info("Cannot scrape the HTML for")
            return race_links

        soup = BS(html, "lxml")

        if not today:
            race_results_window = soup.find(
                "section", attrs={"id": "archiveFormList"})
            result_card_sections = (
                race_results_window.find_all(
                    "div", class_="w-results-holder")[1:]
                if race_results_window
                else []
            )

        else:
            race_results_window = soup.find(
                "div", attrs={"id": "RacecardGrid"})
            result_card_sections = (
                race_results_window.find_all(
                    "div", class_="w-racecard-grid-meeting")
                if race_results_window
                else []
            )

        for result_card_section in result_card_sections:
            if not today:
                if "IRE" in result_card_section.section.h2.text:
                    continue
                sections = result_card_section.find_all(
                    "div",
                    style="width:100% !important; min-height:234px;border-right:none;border-bottom:none;max-height:234px;",
                )
            else:
                if "IRE" in result_card_section.div.a.h2.text:
                    continue
                sections = result_card_section.find_all(
                    "li", class_="w-racecard-grid-race-inactive"
                )

            for index, title_link in enumerate(sections, 1):
                url = "https://www.timeform.com" + title_link.a["href"]

                if not today:
                    race_title_text = title_link.text.upper()
                    code = None
                else:
                    race_title_text = title_link["title"].upper()
                    code = title_link.a.span.text.split(" ")[1]

                cleaned_race_definition_word_list = race_title_text.replace(
                    "'", "").replace("NOVICES", "NOVICE").split()
                race_type_name = get_race_type_name(
                    cleaned_race_definition_word_list)

                race_links.append((url, race_type_name, code, index))

        return race_links

    def get_race_datetime(self, html, race_type):
        if not html:
            LOGGER.error(
                "Could not scrape %s because of broken HTML" % str(html))
            return []

        soup = BS(html, "lxml")
        race_header = soup.find("section", attrs={"id": "rp-header"})
        header_rows = race_header.find_all("tr")

        if len(header_rows) < 2:
            LOGGER.warning("Could not fetch DATE and TIME from")
            return []

        race_datetime = header_rows[0].h2.text.split()

        if len(race_datetime) != 5:
            LOGGER.warning("Could not fetch DATE and TIME from")
            return []

        race_time = race_datetime[0]
        race_date_str = " ".join(race_datetime[1:])

        try:
            race_date = dt.datetime.strftime(
                dt.datetime.strptime(
                    race_date_str, "%a %d %B %Y"), "%-d/%-m/%y"
            )
        except ValueError:
            race_date = dt.datetime.strftime(
                dt.datetime.strptime(
                    race_date_str, "%A %d %B %Y"), "%-d/%-m/%y"
            )

        distance_of_the_race = header_rows[1].find_all("td")[-1].text
        self.date_and_time["date"] = race_date
        self.date_and_time["time"] = race_time

        self.date_and_time['#'] = None

        date_and_time_section = soup.find(
            "span", class_="rp-title-course-name")

        if date_and_time_section:
            self.date_and_time["track"] = date_and_time_section.text.title(
            ).strip()
        else:
            title_text = soup.find("h1", class_="rp-title").text
            self.date_and_time["track"] = (
                " ".join(title_text.split()[:-1]).title().strip()
            )

        distance = (
            distance_of_the_race.split(":")[-1]
            .replace("(Inner)", "")
            .replace(" (Old)", "")
            .replace(" (XC)", "")
            .replace(" (New)", "")
            .strip()
        )
        if "y" in distance:
            distance = ' '.join(distance.split(' ')[0:-1])

        self.date_and_time["distance"] = distance

        self.date_and_time["race_type"] = race_type
        return self.date_and_time

    def get_race_info_before(self, html, raw_code, tips_data):
        data_list = []
        soup = BS(html, "lxml")

        main_window = soup.find("div", attrs={"id": "PassBody"})

        if not main_window:
            LOGGER.warning(
                "Could not find PassBody because of the race did not start yet"
            )
            return []

        main_table = main_window.find("table", attrs={"id": "race-pass-body"})
        tbodies = main_table.find_all("tbody", class_="rp-table-row")

        for tbody in tbodies:
            local_race_data = {}
            trs = tbody.find_all("tr")

            upper_tds = trs[0].find_all("td")
            lower_tds = trs[1].find_all("td")
            local_race_data.update(self.date_and_time)
            local_race_data["#"] = raw_code[3]

            code = soup.find("span", title="Surface of the race")
            if code:
                code = code.text
            else:
                code = raw_code[2]
            if code == "Turf":
                code = "F"
            elif code == "Hurdle":
                code = "H"
            elif code == "Chase":
                code = "C"
            elif code == "Bumper":
                code = "B"
            else:
                code = "A"
            if local_race_data.get("race_type") == "blank":
                code = "b"
            local_race_data["code"] = code

            runners = str(len(tbodies))
            local_race_data["runners"] = runners

            horse_name = upper_tds[2].text.split(
                ".")[-1].split("(")[0].replace('\n', '').strip()
            local_race_data["horse_name"] = horse_name
            jokey = upper_tds[3].text.replace("\n", '').replace(
                r"^[a-zA-Z0-9!@#\$%\^\&amp;*\)\(+=._-pting+$/g", "").strip()
            if "(" in jokey:
                jokey = jokey.split("(")[0]
            local_race_data["jokey"] = jokey

            trainer = lower_tds[3].text.replace(
                '\n', '').replace('NT', '').strip()
            if "(" in trainer:
                trainer = trainer.split("(")[0].strip()
            local_race_data["trainer"] = trainer

            horse_age = upper_tds[5].text.strip()
            local_race_data["horse_age"] = horse_age

            horse_weight = upper_tds[6].text.strip()
            if "(" in horse_weight:
                horse_weight = horse_weight.split("(")[0].strip()
            local_race_data["horse_weight"] = horse_weight
            try:
                local_race_data["position"] = upper_tds[0].find_all("span")[
                    0].text
            except IndexError:
                local_race_data["position"] = lower_tds[0].find_all("span")[
                    0].text

            local_race_data["tips"] = tips_data.get(
                horse_name, (None, None))[0]

            local_race_data["tips_rating"] = tips_data.get(
                horse_name, (None, None))[1]

            row = list(local_race_data.values())
            data_list.append(row)
        return data_list

    def get_race_info_after(self, html, sharp) -> list:
        race_data = []
        soup = BS(html, "lxml")

        main_window = soup.find("div", attrs={"id": "ReportBody"})

        if not main_window:
            LOGGER.warning(
                "Could not find ReportBody on because of the race did not start yet"
 
            )
            return []

        main_table = main_window.find("table", class_="rp-table rp-results")
        tbodies = main_table.find_all("tbody", class_="rp-table-row")

        winner_bsp = None
        winner_high = None
        for tbody in tbodies:
            local_race_data = {}
            trs = tbody.find_all("tr")

            upper_tds = trs[0].find_all("td")
            lower_tds = trs[1].find_all("td")
            local_race_data.update(self.date_and_time)
            local_race_data["#"] = sharp

            code = soup.find("span", title="The type of race").text
            if code == "Flat":
                code_type = soup.find("span", title="Surface of the race").text
                if code_type == "Turf":
                    code = "F"
                else:
                    code = "A"
            elif code == "Hurdle":
                code = "H"
            elif code == "Chase":
                code = "C"
            elif code == "Bumper":
                code = "B"
            else:
                code = "A"
            if local_race_data.get("race_type") == "blank":
                code = "b"
            local_race_data["code"] = code

            runners = str(len(tbodies))
            local_race_data["runners"] = runners

            horse_name = upper_tds[4].text.split(".")[-1].split("(")[0].strip()
            local_race_data["horse_name"] = horse_name

            jokey = upper_tds[10].text.replace("\n", "").replace(
                r"^[a-zA-Z0-9!@#\$%\^\&amp;*\)\(+=._-pting+$/g", "").strip()
            if "(" in jokey:
                jokey = jokey.split("(")[0]
            local_race_data["jokey"] = jokey

            trainer = lower_tds[3].text.strip()
            if "(" in trainer:
                trainer = trainer.split("(")[0].strip()
            local_race_data["trainer"] = trainer

            horse_age = upper_tds[11].text.strip()
            local_race_data["horse_age"] = horse_age

            horse_weight = upper_tds[12].text.strip()
            if "(" in horse_weight:
                horse_weight = horse_weight.split("(")[0]
            local_race_data["horse_weight"] = horse_weight
            try:
                local_race_data["position"] = upper_tds[0].find_all("span")[
                    0].text
            except IndexError:
                local_race_data["position"] = lower_tds[0].find_all("span")[
                    0].text

            local_race_data["tips"] = None

            local_race_data["tips_rating"] = None

            try:
                high, low = trs[0].find_all("td")[16].text.strip().split("/")
            except IndexError:
                LOGGER.critical(
                    "Cookies have been expired for"[0])
                print("\nATTENTION: Your Cookies expired!\nPlease UPDATE cookies!\n")
                exit()
            if len(trs[0].find_all("td")) >= 16:
                local_race_data["high"] = float(high) if high.replace(".", "").isdigit() else 1000
                local_race_data["low"] = float(low) if low.replace(".", "").isdigit() else 0
            else:
                local_race_data["high"], local_race_data["low"] = None, None
            bsp = str(upper_tds[15].text.strip())
            bpsp = str(lower_tds[7].text.replace("(", "").replace(")", "").strip())
            local_race_data["bsp"] = float(bsp) if bsp and bsp.replace('.', '').isdigit() and bsp.count('.') <= 1 else bsp
            local_race_data["bpsp"] = float(bpsp) if bpsp and bsp.replace('.', '').isdigit() and bsp.count('.') <= 1 else bpsp
            horse_number = trs[0].find_all("td")[0].find_all("span")[0].text

            if horse_number == "1":
                winner_high = local_race_data["high"]
                winner_bsp = local_race_data["bsp"]

            local_race_data["winner_high"] = winner_high
            local_race_data["winner_bsp"] = winner_bsp

            row = list(local_race_data.values())
            race_data.append(row)
        return race_data

    def yesterday_result(self, html, url):
        if not self.get_race_datetime(html, url[1]):
            return self.race_data
        data = self.get_race_info_after(html, url[3])
        
        return data

########################################
############# TODAY SCRAPER ############
########################################


def today_scraper() -> list:
    code_for_iter = None
    today_data_list = []
    scraper = RaceScraper()

    today_html = get_html_page(HOME_URL, COOKIES)
    
    today_all_race_urls = scraper.get_race_venues(today_html, True)

    today_instance = RaceScraper()
    for tod_url in today_all_race_urls:
        
        if tod_url[1] != code_for_iter:
            tips_data = get_html_page(
                "https://www.timeform.com/horse-racing/tips/" + tod_url[0].split('/')[-6] + "-best-bets-today/" + tod_url[0].split('/')[-3], COOKIES)
            if isinstance(tips_data, int):
                LOGGER.info("HTML page could not be fetched from %s" % tod_url[0])
                continue

            tips_data_soup = BS(tips_data, "lxml")
            tips_data_soup = tips_data_soup.find_all(
                "div", class_="widget-content w-rc-tips-race")
            tips_data = {}
            for race in tips_data_soup:
                runners = race.find_all(
                    "div", class_="w-rc-tips-entry w-rc-tips-entry-runner")
                for position, runner in enumerate(runners, 1):
                    horse_name = runner.a.text.replace("\r\n", "").strip()
                    if "(" in horse_name:
                        horse_name = horse_name.split("(")[0].strip()
                    tips_rating = len(runner.find_all("div")
                                      [1].find_all("img"))
                    tips_data.update({horse_name: (position, tips_rating)})

        code_for_iter = tod_url[1]
        html = get_html_page(tod_url[0], COOKIES)

        if not html:
            continue
        today_instance.get_race_datetime(html, tod_url[1])
        today_result = today_instance.get_race_info_before(
            html, tod_url, tips_data)
        for row in today_result:
            today_data_list.append(tuple(row))


    return today_data_list


#######################################
########### ONE-DAY SCRAPER ###########
#######################################

def day_scraper(date: str) -> list:
    scraper = RaceScraper()
    print('Date:', date)
    date_for_db = '/'.join(date.split('-')[::-1])
    if date_for_db[3] == '0':
        date_for_db = date_for_db[:3] + date_for_db[4:]
    if date_for_db.startswith('0'):
        date_for_db = date_for_db[1:]
    date_for_db = date_for_db[:-4] + date_for_db[-2:]


    all_time_html = get_html_page(
        'https://www.timeform.com/horse-racing/results/' + date, COOKIES)
    all_urls = scraper.get_race_venues(all_time_html)


    instance = RaceScraper()

    data_list = []
    
    for url in all_urls:
        print('URL:', url)
        html = get_html_page(url[0], COOKIES)
        time.sleep(1)
        if not html:
            continue
        result = instance.yesterday_result(html, url)
        time.sleep(4.7)
        if result:
            data_list.extend(result)

    return data_list

# if __name__ == '__main__':
#     print(day_scraper('2021-11-30'))