from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable, Optional

import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
from custom_components.movie_times.const import *
from custom_components.movie_times.scraper import *

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=1)
THEATER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_THEATER_NAME): cv.string,
        vol.Required(CONF_SCRAPER): cv.string,
        vol.Optional(CONF_THEATER_ID): cv.string,
        vol.Optional(CONF_SHOW_DETAILS): cv.boolean,
        vol.Optional(CONF_SHOW_SCREEN): cv.boolean,
        vol.Optional(CONF_SPLIT_FORMATS): cv.boolean,
    }
)
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_NUM_DAYS): cv.positive_int,
        vol.Optional(CONF_PAST_SHOWS): cv.boolean,
        vol.Required(CONF_THEATERS): vol.All(cv.ensure_list, [THEATER_SCHEMA]),
    }
)

async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    sensors = []
    for theater_conf in config.get(CONF_THEATERS):
        scraper = None
        if theater_conf.get(CONF_SCRAPER) == "brattle":
            scraper = BrattleScraper(theater_conf.get(CONF_SHOW_DETAILS))
        elif theater_conf.get(CONF_SCRAPER) == "coolidge":
            scraper = CoolidgeScraper(theater_conf.get(CONF_SHOW_DETAILS),
                                      theater_conf.get(CONF_SHOW_SCREEN))
        elif theater_conf.get(CONF_SCRAPER) == "somerville":
            scraper = FrameOneScraper("https://somervilletheatre.com/wp-content/themes/somerville/showtimes.xml",
                                      theater_conf.get(CONF_SHOW_SCREEN))
        elif theater_conf.get(CONF_SCRAPER) == "capitol":
            scraper = FrameOneScraper("https://www.capitoltheatreusa.com/wp-content/themes/capitoltheatre/showtimes.xml",
                                      theater_conf.get(CONF_SHOW_SCREEN))
        elif theater_conf.get(CONF_SCRAPER) == "fandango":
            scraper = FandangoScraper(theater_conf.get(CONF_THEATER_ID) or "",
                                      theater_conf.get(CONF_SPLIT_FORMATS))
        sensors.append(
            MovieTimesSensor(
                theater_conf.get(CONF_THEATER_NAME),
                config.get(CONF_NUM_DAYS) or 0,
                config.get(CONF_PAST_SHOWS) or False,
                scraper
            )
        )
    async_add_entities(sensors, update_before_add=True)


class MovieTimesSensor(Entity):
    def __init__(
        self,
        theater_name,
        days,
        filter_past_shows,
        scraper
    ):
        self._sensor_name = theater_name
        self._theater_name = theater_name
        self._days = days
        self._filter_past_shows = filter_past_shows
        self._scraper = scraper
        self._attr = None
        self._state = None

    @property
    def name(self):
        return self._sensor_name

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attr

    def update(self) -> None:
        theater_data = {}
        theater_data["name"] = self._theater_name
        showtimes = []
        for i in range(self._days + 1):
            day = {}
            day["day"] = (datetime.today() + timedelta(days=i)).date().isoformat()
            day["showtimes"] = self._scraper.scrape(i, self._filter_past_shows)
            showtimes.append(day)
        theater_data["days"] = showtimes
        self._attr = {STATE_ATTR_MOVIE_TIMES: theater_data}
        self._state = "OK"
