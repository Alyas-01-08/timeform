import time
import logging

import requests
import cloudscraper
from requests.exceptions import ConnectionError as CloudConnectionError


from browser import  get_cookies
from settings import RACE_TYPE_NAMES, PATH, HEADERS


######################################################################
####################### LOGGING CONFIGURATIONS #######################
######################################################################
LOGGER = logging.getLogger("Timeform")
handler = logging.FileHandler(PATH + "/logs.log")
formater = logging.Formatter(
    "%(asctime)s| %(message)s ---> %(lineno)s", "%Y-%m-%d %H:%m"
)
handler.setFormatter(formater)
LOGGER.addHandler(handler)
level = logging.INFO
LOGGER.setLevel(level)
######################################################################



def get_html_page(url, cookies):
    engine = cloudscraper.create_scraper()
    try:
        html_page_request = engine.get(
            url=url, headers=HEADERS, cookies=cookies, timeout=11
        )
    except CloudConnectionError:
        LOGGER.info(
            "HTML page could not be fetched because of the Connection Error, settings Cookies have been used instead"
        )
        return 0
    except requests.exceptions.ReadTimeout:
        LOGGER.info("The program has freezed and got Timeout Error")
        return {}

    if html_page_request.status_code == 200:
        return html_page_request.text

    LOGGER.info(
        "HTML page could not be fetched because of the response %d"
        % html_page_request.status_code
    )
    time.sleep(10)
    return 0



def get_race_type_name(header):
    match_results = {}
    most_matched = 0
    most_matched_key = 0

    for number, race_name_list in RACE_TYPE_NAMES.items():
        words_found = 0
        for word in header:
            if word.title() in race_name_list:
                words_found += 1
        match_results[number] = words_found


    for key, value in match_results.items():
        if value > most_matched:
            most_matched = value
            most_matched_key = key

    
    header_name = ' '.join(RACE_TYPE_NAMES[most_matched_key])
    return header_name
