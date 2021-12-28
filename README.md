# Movie Times for Home Assistant
This project defines a sensor that puts movie times in its attributes.

Unfortunately, I couldn't find any APIs for movie times that weren't far too expensive for this sort of thing, and I'm not super convinced those APIs would have accurate data for the smaller theaters I tend to go to. So I had to fall back on scraping the websites, and only implemented the theaters I care about.

So if you don't live in Massachusetts or don't like the same four theaters I like best (The Brattle, Coolidge Corner, the Somerville Theatre, and the Capitol Theater), this component won't be useful.

I might add more theaters later, but honestly, I probably won't bother.

## Installation
Throw the files in `custom_components` or point HACS at this repo.

For the config file, put in something like this:
```
sensor:
  - platform: movie_times
    name: Movie Times
    next_days: 0
    filter_past_shows: true
    theaters:
      - theater_name: The Brattle
        show_screen: false
        show_details: true
      - theater_name: Coolidge Corner
        show_screen: true
        show_details: true
      - theater_name: Somerville Theatre
        show_screen: true
        show_details: true
      - theater_name: Capitol Theatre
        show_screen: true
        show_details: true
```
`next_day` is the number of days into the future to include — `0` means to only show today, `1` means to show today and tomorrow, and so on. It's probably useless to make this very big, because not all of these theaters schedule stuff very far out. This is optional and defaults to `0`.

`filter_past_shows` controls whether or not showtimes today that have already happened will appear. This is optional and defaults to `false`. By default, the sensor updates hourly, so this might be a little delayed if enabled.

For now, this only works with the `theater_name`s listed in the example. `show_screen` and `show_details` are optional, and both default to `false`. Each theater gives different details, but it's usually stuff like the format or what rep series a screening falls under. For single screen theaters, like The Brattle, `show_screen` will always be `1`.
