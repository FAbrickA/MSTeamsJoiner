# MSTeamsJoiner
Bot to attend MS Teams meetings.

My purpose was to create working, flexible and easy to read 
and improve bot. I wrote it for my lectures, so you may need 
to do some changes for your meetings. Feel free to fork or
contribute the project.  

This is the early version, so some bugs can occure.

### What it is doing, shortly
Log in MS Teams, go to every needed Team. If some Team will 
have a meeting, join it. Using special algorythm, consider 
if it needed to leave the meeting. And then after pause
repeat checking Teams, ignoring last joined Team.

### Installation
1. Install requirements:  
```
pip install -r requirements.txt
```
2. Install chromedriver:
   * Check your Chrome version. To get it, open 
   Chrome > Settings > About Chrome
   * If your version is 114 or older:  
      > Go [here](https://chromedriver.storage.googleapis.com/index.html)
      and download your version  

      If your version is 115 or newer:
      > Go [here](https://googlechromelabs.github.io/chrome-for-testing/#stable),
      find the right link in the table and download your version
   * Put your chromedriver in `./driver/chromedriver/`
3. Rename `config.example.json` to `config.json`, open it and
fulfill necessary fields.
4. Run as `python main.py`

### Manage config.json
* *email* and *password* - data to log in.
* *min_attenders* - instant leaving the meeting if number
of attenders drop to this value.
* *attenders_threshold* - instant leaving the meeting if 
only this percent of people remain in meeting.
* *meeting_check_interval* - pause between two meeting checks.
* *headless* - run chrome in headless mode (invisible)
* *mute_audio* - you won't be able to hear something from
meeting.
* *driver_path* - path to your chromedriver.
* *discord_webhook_url* - webhook for discord notifications. 
Remain empty if you don't need them.
* *white_list* - check only Teams with these titles. Remain
empty if you don't need white_list functionality.
* *black_list* - ignore Teams with these titles.

#### Howto Discord Webhooks
[Read this tutorial](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)

### How bot works
#### How white_list and black_list works
If *white_list* is not empty:
1. Find every Team that matches *white_list*
2. From this set delete every Team that matches *black_list*

Else:
1. Get all Teams that doesn't match *black_list*

#### How leaving algorythm works
1. Every 5 seconds it checks number of attenders (*n*).
2. Then update *max_attenders* value: `max(n, max_attenders)`
3. Bot waits until *max_attenders* become >= 15. So, it won't
leave the meeting if *max_attenders* < 15.
4. Then *max_attenders* >= 15, it will leave if one of these 
events happen:
   * *n* < *min_attenders*.
   * (*n* / *max_attenders*) <= *attenders_threshold*.