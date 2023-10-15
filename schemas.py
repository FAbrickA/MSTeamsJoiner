from sqlite3 import Connection
from typing import Optional

from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from db.tables import teams
from utils import limit_str


class Team:
    def __init__(
            self,
            title: str,
            elem: Optional[WebElement] = None,
    ):
        self.title = title
        self.elem = elem
        self.link = None

        self.id: Optional[int] = None  # teams.id in database

    def __repr__(self):
        return f"<Team: \"{limit_str(self.title, 120)}\">"

    @staticmethod
    def get_team_title_by_elem(elem: WebElement) -> str:
        title = elem.get_attribute("aria-label")
        return title

    @classmethod
    def parse_team(cls, elem: WebElement) -> "Team":
        title = cls.get_team_title_by_elem(elem)
        return Team(title, elem=elem)

    def update_elem(self, driver: WebDriver):
        """
        Finds WebElement of the team and writes it to self.elem

        You need to do update_elem() every time if you need to use this
        element and the old one is expired.
        """

        self.elem = driver.find_element(By.CSS_SELECTOR, f"[aria-label='{self.title}']")

    def get_channel_with_meeting(self, driver: WebDriver) -> Optional["Channel"]:
        """
        Get Channel that have active meeting or None. We will call this
        channel "active".

        You should be on current Team page to call this function.
        """

        channels_block = driver.find_element(By.CSS_SELECTOR, "ul.school-app-team-channel")
        try:
            meeting_icon = channels_block.find_element(By.CSS_SELECTOR, "active-calls-counter")
        except exceptions.NoSuchElementException:
            return None
        else:  # found active_channel
            active_channel_elem = driver.execute_script(
                "return arguments[0].closest('li.animate-channel-item');",
                meeting_icon
            )
            active_channel = Channel.parse_channel(self, active_channel_elem)
            return active_channel


class Channel:
    def __init__(
            self,
            team: Team,
            data_tid: str,
            elem: Optional[WebElement] = None,
            link: Optional[str] = None  # not supported yet
    ):
        self.team = team
        self.data_tid = data_tid
        self.elem = elem
        self.link = link

    def update_elem(self, driver: WebDriver):
        """
        Finds WebElement of the team and writes it to self.elem

        You need to do update_elem() every time if you need to use this
        element and the old one is expired.
        """

        self.elem = driver.find_element(f"li.animate-channel-item[data-tid='{self.data_tid}']")

    @classmethod
    def parse_channel(cls, team: Team, elem: WebElement) -> "Channel":
        data_tid = elem.get_attribute("data_tid")
        return Channel(team, data_tid, elem=elem)

