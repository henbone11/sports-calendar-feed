# Auto-updating Proton sports calendar

This repository publishes a subscription-ready sports calendar for Proton Calendar.

## Calendar URL

After GitHub Pages is enabled from the `docs` folder, subscribe to:

`https://henbone11.github.io/sports-calendar-feed/sports_calendar.ics`

## Included categories

- Major MMA and boxing events maintained in the source list
- Indianapolis Colts
- Indiana Fever
- Formula 1
- MotoGP

## Updates

GitHub Actions refreshes the feed every Monday and can also be run manually from the Actions tab.

## Time zone

Events use fixed UTC-05:00 (`Etc/GMT+5`) as requested. This does not observe daylight-saving time.

## Limitations

Combat-sports cards, start times, and streaming rights change frequently. The feed uses structured schedule sources where available and retains manually maintained combat-sports entries until they can be confirmed or replaced.
