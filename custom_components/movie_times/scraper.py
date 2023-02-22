import requests
import logging
import json
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo
from datetime import datetime, date, timedelta, timezone

_LOGGER = logging.getLogger(__name__)

def get_brattle_showtimes(theater_id, days_from_now=0, filter_past_shows=True, show_details=True, show_screen=True):
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
                if show_screen:
                    # single screen here, so I guess I'll put everthing in "1"?
                    showtime_data["screen"] = "1"
                show_data["times"].append(showtime_data)

        if show_details:
            details = []
            for detail in show.select_one(".show-description").select(".pill"):
                details.append(detail.text)
            show_data["details"] = details

        # Only add the movie if there are still showtimes left
        if not filter_past_shows or len(show_data["times"]) > 0:
            shows.append(show_data)
    return shows


def get_coolidge_showtimes(theater_id, days_from_now=0, filter_past_shows=True, show_details=True, show_screen=True):
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
                if show_screen:
                    showtime_data["screen"] = showtime.select_one(".showtime-ticket__venue").text
                show_data["times"].append(showtime_data)

        if show_details:
            details = []
            for detail in film_card.select(".film-program__title"):
                details.append(detail.text)
            show_data["details"] = details

        if not filter_past_shows or len(show_data["times"]) > 0:
            shows.append(show_data)
    return shows


def get_somerville_showtimes(theater_id, days_from_now=0, filter_past_shows=True, show_details=True, show_screen=True):
    return get_frame_one_showtimes(
        "https://somervilletheatre.com/wp-content/themes/somerville/showtimes.xml",
        days_from_now=days_from_now,
        filter_past_shows=filter_past_shows,
        show_details=show_details,
        show_screen=show_screen,
    )


def get_capitol_showtimes(theater_id, days_from_now=0, filter_past_shows=True, show_details=True, show_screen=True):
    return get_frame_one_showtimes(
        "https://www.capitoltheatreusa.com/wp-content/themes/capitoltheatre/showtimes.xml",
        days_from_now=days_from_now,
        filter_past_shows=filter_past_shows,
        show_details=show_details,
        show_screen=show_screen,
    )


def get_frame_one_showtimes(url, days_from_now=0, filter_past_shows=True, show_details=True, show_screen=True):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0"}
    raw_html = requests.get(url, headers=headers).text
    data = BeautifulSoup(raw_html, "html.parser")

    shows = []

    # Both of this company's theaters are in MA, so it's safe to assume EST
    todays_date_EST = datetime.today().replace(tzinfo=timezone.utc).astimezone(tz=ZoneInfo("America/New_York"))
    target_date = todays_date_EST + timedelta(days=days_from_now)

    film_titles = data.find_all("filmtitle")
    for film_title in film_titles:
        show_data = {}
        show_data["name"] = film_title.find("name").text.title()
        show_data["times"] = []
        had_show_on_target_date = False
        for show in film_title.find_all("show"):
            show_date_raw = show.find("date").text
            show_time_raw = show.find("time").text
            show_date = datetime(
                int(show_date_raw[-4:]),
                int(show_date_raw[:2]),
                int(show_date_raw[2:4]),
                hour=int(show_time_raw[:2]),
                minute=int(show_time_raw[2:]),
                tzinfo=ZoneInfo("America/New_York"),
            )
            is_target_date = show_date.date() == target_date.date()
            if is_target_date and (not filter_past_shows or days_from_now > 0 or show_date > target_date):
                showtime_data = {}
                showtime_data["time"] = show_date.strftime("%I:%M %p").lower().removeprefix("0")
                if show.find("salelink"):
                    showtime_data["link"] = show.find("salelink").text
                if show_screen:
                    showtime_data["screen"] = show.find("screen").text
                show_data["times"].append(showtime_data)
            had_show_on_target_date = had_show_on_target_date or is_target_date
        if had_show_on_target_date and (not filter_past_shows or len(show_data["times"]) > 0):
            shows.append(show_data)
    return shows

def get_fandango_showtimes(theater_id, days_from_now=0, filter_past_shows=True, show_details=True, show_screen=True):
    url_template = "https://www.fandango.com/napi/theaterMovieShowtimes/{}?date={}"
    url = url_template.format(theater_id, (date.today() + timedelta(days=days_from_now)).isoformat())
    headers = {"Referer": "https://www.fandango.com"}
    raw_json = requests.get(url, headers=headers).text
    data = json.loads(raw_json)['viewModel']['movies']
    shows = []
    for film in data:
        for variant in film['variants']:
            variant_suffix = "" if variant['format'] == 'Standard' else variant['format']
            show_data = {}
            show_data['name'] = film['title'] + variant_suffix
            show_data['times'] = []
            for amenity_group in variant['amenityGroups']:
                for showtime in amenity_group['showtimes']:
                    show_date = datetime.strptime(showtime['ticketingDate'], "%Y-%m-%d+%H:%M")
                    showtime_data = {}
                    showtime_data["time"] = show_date.strftime("%I:%M %p").lower().removeprefix("0")
                    showtime_data["link"] = showtime['ticketingJumpPageURL']
                    if not filter_past_shows or not showtime['expired']:
                        show_data['times'].append(showtime_data)
            shows.append(show_data)
    return shows
