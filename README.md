# Movie Times for Home Assistant
This project defines a sensor that puts movie times in its attributes. I mostly just use this because I like seeing this kind of info on a dashboard I keep around, but who knows, maybe you could use it for some kind of funky automation or something...

Unfortunately, I couldn't find any legit APIs for movie times that weren't way too expensive for this sort of thing, and I'm not super convinced those APIs would have accurate data for the smaller theaters I tend to go to. So I had to fall back on scraping the websites, and only implemented the theaters I care about. Eventually, I noticed that Fandango has an undocumented API that wasn't too tricky to figure out, so now this integration can now handle any theater on there. Of course, this is an official API, so this could fall apart at any time.

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
      # To find the id, look for the five character code in the URL, for example, Landmark Kendall Square's
      # URL is https://www.fandango.com/landmark-kendall-square-cinema-aaeis/theater-page and it's ID is "AAEIS"
      - theater_name: Landmark Kendall Square
        scraper: fandango
        theater_id: AAEIS

      # These theaters have more info (the "details" field and the theater number),
      # but they're only going to be useful if you live in metro Boston
      - theater_name: The Brattle Showtimes
        scraper: brattle
        show_details: true
      - theater_name: Coolidge Corner Showtimes
        scraper: coolidge
        show_screen: true
        show_details: true
      - theater_name: Somerville Theatre Showtimes
        scraper: somerville
        show_screen: true
        show_details: true
      - theater_name: Capitol Theatre Showtimes
        scraper: capitol
        show_screen: true
        show_details: true
```
`next_day` is the number of days into the future to include — `0` means to only show today, `1` means to show today and tomorrow, and so on. It's probably useless to make this very big, because not all of these theaters schedule stuff very far out. This is optional and defaults to `0`.

`filter_past_shows` controls whether or not showtimes today that have already happened will appear. This is optional and defaults to `false`. By default, the sensor updates hourly, so this might be a little delayed if enabled.

For now, this only works with the `theater_name`s listed in the example. `show_screen` and `show_details` are optional, and both default to `false`. Each theater gives different details, but it's usually stuff like the format or what rep series a screening falls under. For single screen theaters, like The Brattle, `show_screen` will always be `1`.

## Frontend
I didn't bother making a real lovelace card for this, but here's a couple quick and dirty options you could try out if you install [Lovelace HTML Jinja2 Template Card](https://github.com/PiotrMachowski/Home-Assistant-Lovelace-HTML-Jinja2-Template-card) and [Decluttering Card](https://github.com/custom-cards/decluttering-card)

<details><summary>Show Lovelace YAML</summary>
<p>
```
  movie_showtime_card:
    default:
      - header_text: Change Me!
      - theater_entity: Change Me!
    card:
      type: custom:html-template-card
      title: '[[header_text]]'
      ignore_line_breaks: true
      entities: '[[theater_entity]]'
      content: |
        <div class="movie-container">
          {% for movie in state_attr('[[theater_entity]]','movie_times')['days'][0]['showtimes'] %}
          <div class="movie">
            <div class="movie-title">
              {{ movie['name'] }}
            </div>
            {% if movie['details'] != Null %}
            {% for detail in movie['details'] %}
            {% if loop.first %}
              <br>
            {% endif %}
            <div class='detail'>
              {{ detail }}
            </div>
            {% endfor %}
            {% endif %}
            <div class="showtime-container">
              {% for show in movie['times'] %}
              <a target="_blank" rel="noopener noreferrer" {% if show['link'] != Null %} href="{{show['link']}} {% endif %}">
                <div class="showtime">
                  {{show['time']}}
                  {% if show['screen'] != Null %}
                  <br>
                  <span class="theater-label">Theater </span>{{show['screen']}}
                  {% endif %}
                </div>
              </a>
              {% endfor %}
            </div>
          </div>
          {% else %}
          <div class="movie">
            <div class="movie-title">
              No Showtimes
            </div>
          </div
          {% endfor %}
        </div>
        <style>
          .movie-container {
            display: flex;
            flex-flow: row wrap;
            justify-content: flex-start;
            gap: 7.5px;
          }
          .movie {
            background: var( --ha-card-background, var(--card-background-color, white) );
            border-radius: var(--ha-card-border-radius, 10px);
            box-shadow: var( --ha-card-box-shadow, 0px 2px 1px -1px rgba(0, 0, 0, 0.2), 0px 1px 1px 0px rgba(0, 0, 0, 0.14), 0px 1px 3px 0px rgba(0, 0, 0, 0.12) );
            padding: 10px;
          }
          @media all and (min-width:600px) {
            .movie {
              width: calc(50% - 10px - 20px);
            }
          }
          @media not all and (min-width:600px) {
            .movie {
              width: 100%;
            }
          }
          .movie-title {
            padding-top: 0px;
            padding-left: 0.25em;
            font-size: 1.2em;
            font-variant: small-caps;
            display: inline;
          }
          .detail {
            font-size: 0.8em;
            color: var(--disabled-text-color);
            padding: 2.5px;
            padding-right: 5px;
            padding-left: 5px;
            margin-right: 1em;
            display: inline-block;
            text-align: center;
          }
          .showtime-container {
            display: flex;
            flex-flow: row wrap;
            justify-content: flex-start;
            gap: 5px;
            margin-top: 10px;
            margin-bottom: 10px;
          }
          .showtime {
            font-size: 1em;
            background: var(--background-color);
            padding: 5px;
            padding-right: 10px;
            padding-left: 10px;
            border-radius: var(--ha-card-border-radius, 4px);
            display: inline-block;
            text-align: center;
          }
          .theater-label {
            font-size: 0.65em;
            vertical-align: top;
            color: var(--disabled-text-color);
          }
          a {
            color: inherit;
            text-decoration: inherit;
          }
          ha-card {
            background: none;
            box-shadow: none;
          }
        </style>

  compact_movie_showtime_card:
    default:
      - header_text: Change Me!
      - theater_entity: Change Me!
    card:
      type: custom:html-template-card
      title: '[[header_text]]'
      ignore_line_breaks: true
      entities: '[[theater_entity]]'
      content: |
        <div class="movie-container">
          {% for movie in state_attr('[[theater_entity]]','movie_times')['days'][0]['showtimes'] %}
          <div class="movie">
            <div class="movie-title">
              {{ movie['name'] }}
            </div>
            <div class="showtime-container">
              {% for show in movie['times'] %}
              <a target="_blank" rel="noopener noreferrer" {% if show['link'] != Null %} href="{{show['link']}} {% endif %}">
                <div class="showtime">
                  {{show['time']}}
                </div>
              </a>
              {% endfor %}
            </div>
          </div>
          {% else %}
          <div class="movie">
            <div class="movie-title">
              No Showtimes
            </div>
          </div
          {% endfor %}
        </div>
        <style>
          .movie-container {
            justify-content: flex-start;
          }
          .movie {
            display: flex;
            align-items: center;
            background: var( --ha-card-background, var(--card-background-color, white) );
            border-radius: var(--ha-card-border-radius, 4px);
            box-shadow: var( --ha-card-box-shadow, 0px 2px 1px -1px rgba(0, 0, 0, 0.2), 0px 1px 1px 0px rgba(0, 0, 0, 0.14), 0px 1px 3px 0px rgba(0, 0, 0, 0.12) );
            width: 100%;
            padding-bottom: 5px;
          }
          .movie-title {
            padding-top: 0px;
            padding-right: 0.25em;
            font-size: 1.2em;
            font-weight: 600;
            width: 250px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
          .showtime-container {
            display: flex;
            flex-grow: 1;
            gap: 10px;
          }
          .showtime {
            font-size: 0.95em;
            text-align: left;
            width: 65px;
          }
          a {
            color: inherit;
            text-decoration: inherit;
          }
          .card-header {
            font-weight: 600 !important;
            padding-bottom: 5px !important;
            line-height: 32px;
          }
          ha-card {
            padding-left: 22px !important;
            padding-top: 0px !important;
            padding-bottom: 2px !important;
            background: none;
            box-shadow: none;
          }
        </style>
```
</p>
</details>