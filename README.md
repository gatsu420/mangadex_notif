# (Unofficial) Mangadex Notification
Sends you an SMS whenever a new chapter (english translation) is uploaded on Mangadex.

## Functionality
1. Scrape latest chapter (english translation only) from Mangadex's API
2. Post scrape result to DB
3. Send you SMS via Twilio service whenever a new chapter is detected

## Scraped data
1. manga_id (example: integer suffix from https://mangadex.org/title/28804)
2. chapter_id (example: integer suffix from https://mangadex.org/chapter/814044)
3. chapter number (from previous chapter_id, the chapter number would be 14)
4. upload timestamp

## Infra needed
1. Airflow 
2. MariaDB
3. Twilio account (free trial available)

## DB requirement
The script relies on two tables; `manga` for storing master data (manga_id and their titles), and `recent_updates` for storing recent manga updates (all fields in "Scraped data" plus scrape timestamp). The detail goes as follows:
1. `manga`:
    1. `manga_id` (PK)
    2. `title`

2. `recent_updates`
    1. `manga_id` (PK)
    2. `chapter_id`
    3. `chapter_num`
    4. `chapter_timestamp`
    5. `updated_time` (time a record is updated)

You need to manually input manga_id and title to `manga` table. To retrieve manga_id, use integer suffix from https://mangadex.org/title/XXXXX.

## Placeholder (not in order of occurences)
1. `MD_MANGA`: directory to master table in `database_name.table_name` format

2. `MD_RECENT_UPDATE`: directory to recent manga updates table in `database_name.table_name` format

3. `HAKASETEST_HOST`: database address

4. `HAKASETEST_USER`: database username

5. `HAKASETEST_PASS`: database password

6. `TWILIO_SID`: SID for your Twilio account

7. `TWILIO_TOKEN`: auth token for your Twilio account

8. `TWILIO_PHONE_SOURCE`: your Twilio phone number

9. `TWILIO_PHONE_TARGET`: phone number which will receive the SMS

## License 
Copyright (C) 2020 Ranggalawe Istifajar

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see https://www.gnu.org/licenses/.