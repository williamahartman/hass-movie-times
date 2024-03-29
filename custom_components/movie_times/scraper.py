import requests
import logging
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta

_LOGGER = logging.getLogger(__name__)

class Scraper:
    def scrape(self):
        raise NotImplementedError()

class BrattleScraper(Scraper):
    def __init__(self, show_details):
        self._show_details = show_details

    def scrape(self, days_from_now=0, filter_past_shows=True):
        url_template = "https://brattlefilm.org/{}/{}"
        url = url_template.format((date.today() + timedelta(days=days_from_now)).isoformat(), days_from_now)
        raw_html = requests.get(url).text
        data = BeautifulSoup(raw_html, "html.parser")

        shows_raw = data.select(".show-details")
        shows = []
        for show in shows_raw:
            show_data = {}
            show_data["name"] = show.select_one(".show-title").select_one(".title").text

            show_data["times"] = []
            for showtime in show.select(".showtime"):
                if not filter_past_shows or "past" not in showtime.attrs["class"]:
                    showtime_lines = showtime.text.strip().split("\t", 1)
                    showtime_data = {}
                    showtime_data["time"] = showtime_lines[0].strip()
                    if "href" in showtime.attrs:
                        showtime_data["link"] = showtime.attrs["href"]
                    show_data["times"].append(showtime_data)

            if self._show_details:
                details = []
                for detail in show.select_one(".show-description").select(".pill"):
                    details.append(detail.text)
                show_data["details"] = details

            # Only add the movie if there are still showtimes left
            if not filter_past_shows or len(show_data["times"]) > 0:
                shows.append(show_data)
        return shows

class CoolidgeScraper(Scraper):
    def __init__(self, show_details, show_screen):
        self._show_details = show_details
        self._show_screen = show_screen

    def scrape(self, days_from_now=0, filter_past_shows=True):
        url_template = "https://coolidge.org/showtimes?date={}"
        url = url_template.format((date.today() + timedelta(days=days_from_now)).isoformat())
        raw_html = requests.get(url).text
        data = BeautifulSoup(raw_html, "html5lib")

        shows = []
        for film_card in data.select(".film-card"):
            show_data = {}
            show_data["name"] = film_card.select_one(".film-card__title").select_one(".film-card__link").text

            show_data["times"] = []
            for showtime in film_card.select(".showtime-ticket"):
                if not filter_past_shows or "views-row-inactive" not in showtime.parent.parent.attrs["class"]:
                    time_raw = showtime.select_one(".showtime-ticket__time").text
                    time_formatted = time_raw[0:-2] + " " + time_raw[-2:]

                    showtime_data = {}
                    showtime_data["time"] = time_formatted
                    showtime_data["link"] = showtime.parent.attrs["href"]
                    if self._show_screen:
                        showtime_data["screen"] = showtime.select_one(".showtime-ticket__venue").text
                    show_data["times"].append(showtime_data)

            if self._show_details:
                details = []
                for detail in film_card.select(".film-program__title"):
                    details.append(detail.text)
                show_data["details"] = details

            if not filter_past_shows or len(show_data["times"]) > 0:
                shows.append(show_data)
        return shows

class VeeziScraper(Scraper):
    def __init__(self, access_token, site_token, show_screen):
        self._access_token = access_token
        self._site_token   = site_token
        self._show_screen  = show_screen

    def scrape(self, days_from_now=0, filter_past_shows=True):
        target_date = datetime.today() + timedelta(days=days_from_now)
        headers = {"VeeziAccessToken": self._access_token}
        data = json.loads(requests.get("https://api.us.veezi.com/v1/session", headers=headers).text)
        shows_by_title = {}
        for session in data:
            title = session["Title"]
            if title not in shows_by_title:
                shows_by_title[title] = {"name": title,
                                         "times": []}
            show_data = shows_by_title[title]
            show_date = datetime.strptime(session["FeatureStartTime"], "%Y-%m-%dT%H:%M:%S")
            is_target_date = show_date.date() == target_date.date()
            if is_target_date and (not filter_past_shows or days_from_now > 0 or show_date > target_date):
                showtime_data = {}
                showtime_data["time"] = show_date.time().strftime("%I:%M %p").lower().removeprefix("0")
                showtime_data["percent_full"] = int(((session["SeatsSold"] + session["SeatsHeld"] + session["SeatsHouse"]) /
                                                     (session["SeatsSold"] + session["SeatsHeld"] + session["SeatsHouse"] + session["SeatsAvailable"])) * 100)
                if self._show_screen:
                    screen_json = json.loads(requests.get("https://api.us.veezi.com/v1/screen/" + str(session["ScreenId"]), headers=headers).text)
                    showtime_data["screen"] = screen_json["ScreenNumber"]
                if show_date > target_date:
                    showtime_data["link"] = "https://ticketing.useast.veezi.com/purchase/" + str(session["Id"]) + "?siteToken=" + self._site_token
                match session["FilmFormat"]:
                    case "2D Film":
                        showtime_data["details"] = "35mm"
                    case "2D Digital":
                        if "70mm" in session["PriceCardName"]:
                            showtime_data["details"] = "70mm"
                        else:
                            showtime_data["details"] = "DCP"
                    case "3D Digital":
                        showtime_data["details"] = "3D"
                    case "3D HFR":
                        showtime_data["details"] = "3D HFR"
                show_data["times"].append(showtime_data)
        showtime_list = []
        for showtime in shows_by_title.values():
            if showtime["times"]: showtime_list.append(showtime)
        return showtime_list

class FandangoScraper(Scraper):
    def __init__(self, theater_id, separate_formats=True):
        self._theater_id = theater_id
        self._separate_formats = separate_formats

    def scrape(self, days_from_now=0, filter_past_shows=True):
        url_template = "https://www.fandango.com/napi/theaterMovieShowtimes/{}?date={}"
        url = url_template.format(self._theater_id, (date.today() + timedelta(days=days_from_now)).isoformat())
        headers = {"Referer": "https://www.fandango.com"}   # Get a 403 without this header. Surprisingly they don't check the UA
        raw_json = requests.get(url, headers=headers).text
        data = json.loads(raw_json)["viewModel"]["movies"]
        shows = []
        for film in data:
            show_data = {}
            show_data["name"] = self.clean_title(film["title"])
            show_times = []
            for variant in film["variants"]:
                variant_show_data = {}
                variant_show_data["name"] = self.clean_title(film["title"], variant["format"])
                variant_times = []
                for amenity_group in variant["amenityGroups"]:
                    for showtime in amenity_group["showtimes"]:
                        showtime_data = {}
                        showtime_data["link"] = showtime["ticketingJumpPageURL"]
                        showtime_data["time"] = datetime.strptime(showtime["ticketingDate"], "%Y-%m-%d+%H:%M")
                        if not filter_past_shows or not showtime["expired"]:
                            variant_times.append(showtime_data)
                            show_times.append(showtime_data)
                if self._separate_formats:
                    variant_show_data["times"] = list(map(self.clean_showtime, sorted(variant_times, key=lambda i: i["time"])))
                    shows.append(variant_show_data)
            if not self._separate_formats:
                show_data["times"] = list(map(self.clean_showtime, sorted(show_times, key=lambda i: i["time"])))
                shows.append(show_data)
        return shows

    def clean_title(self, title, format="Standard"):
        cleaned_title = re.sub(r'(\(\d{4}\))$', "", title) # Remove the year suffix fandango likes to add
        suffix = "" if format == "Standard" else " (" + format + ")"
        return cleaned_title + suffix

    def clean_showtime(self, showtime_data):
        showtime_data["time"] = showtime_data["time"].strftime("%I:%M %p").lower().removeprefix("0")
        return showtime_data
