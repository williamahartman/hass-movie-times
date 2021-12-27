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

SCAN_INTERVAL = timedelta(hours=1)
THEATER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_THEATER_NAME): cv.string,
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
    async_add_entities([MovieTimesSensor(config)], update_before_add=True)


class MovieTimesSensor(Entity):
    def __init__(self, config):
        self._days = config.get(CONF_NUM_DAYS) or 0
        self._filter_past = config.get(CONF_PAST_SHOWS) or False

        theaters = []
        for theater_conf in config.get(CONF_THEATERS):
            data = {}
            data["name"] = theater_conf.get(CONF_THEATER_NAME)
            data["show_details"] = theater_conf.get(CONF_SHOW_DETAILS) or False
            data["show_screen"] = theater_conf.get(CONF_SHOW_SCREEN) or False
            if data["name"] == "The Brattle":
                data["scrape_method"] = get_brattle_showtimes
            elif data["name"] == "Coolidge Corner":
                data["scrape_method"] = get_coolidge_showtimes
            elif data["name"] == "Somerville Theatre":
                data["scrape_method"] = get_somerville_showtimes
            elif data["name"] == "Capitol Theatre":
                data["scrape_method"] = get_capitol_showtimes
            theaters.append(data)
        self.theaters = theaters
        self._name = config.get(CONF_NAME)
        self._attr = None
        self._state = None

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attr

    def update(self) -> None:
        data = []
        for theater in self.theaters:
            theater_data = {}
            theater_data["name"] = theater["name"]
            showtimes = []
            for i in range(self._days + 1):
                day = {}
                day["date"] = (datetime.today() + timedelta(days=i)).date().isoformat()
                day["showtimes"] = theater["scrape_method"](
                    days_from_now=i,
                    filter_past_shows=self._filter_past,
                    show_details=theater["show_details"],
                    show_screen=theater["show_screen"],
                )
                showtimes.append(day)
            theater_data["showtimes"] = showtimes
            data.append(theater_data)
        self._attr = {STATE_ATTR_MOVIE_TIMES: data}
        self._state = "OK"
