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
        scrape_method = None
        if theater_conf.get(CONF_SCRAPER) == "brattle":
            scrape_method = get_brattle_showtimes
        elif theater_conf.get(CONF_SCRAPER) == "coolidge":
            scrape_method = get_coolidge_showtimes
        elif theater_conf.get(CONF_SCRAPER) == "somerville":
            scrape_method = get_somerville_showtimes
        elif theater_conf.get(CONF_SCRAPER) == "capitol":
            scrape_method = get_capitol_showtimes
        elif theater_conf.get(CONF_SCRAPER) == "fandango":
            scrape_method = get_fandango_showtimes
        sensors.append(
            MovieTimesSensor(
                theater_conf.get(CONF_THEATER_NAME),
                theater_conf.get(CONF_THEATER_ID) or "",
                config.get(CONF_NUM_DAYS) or 0,
                config.get(CONF_PAST_SHOWS) or False,
                theater_conf.get(CONF_SHOW_DETAILS) or False,
                theater_conf.get(CONF_SHOW_SCREEN) or False,
                scrape_method,
            )
        )
    async_add_entities(sensors, update_before_add=True)


class MovieTimesSensor(Entity):
    def __init__(
        self,
        theater_name,
        theater_id,
        days,
        filter_past_shows,
        show_details,
        show_screen,
        scrape_method,
    ):
        self._sensor_name = theater_name
        self._theater_name = theater_name
        self._theater_id = theater_id
        self._days = days
        self._filter_past_shows = filter_past_shows
        self._show_details = show_details
        self._show_screen = show_screen
        self._scrape_method = scrape_method
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
            day["showtimes"] = self._scrape_method(
                theater_id=self._theater_id,
                days_from_now=i,
                filter_past_shows=self._filter_past_shows,
                show_details=self._show_details,
                show_screen=self._show_screen,
            )
            showtimes.append(day)
        theater_data["days"] = showtimes
        self._attr = {STATE_ATTR_MOVIE_TIMES: theater_data}
        self._state = "OK"
