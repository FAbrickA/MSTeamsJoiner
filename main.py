import time
from typing import Optional, Iterable

from selenium.common import exceptions
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from db.connection import connect
from db.tables.teams import approve_team, get_all_teams, TeamRow, insert
from schemas import Team
from settings import settings
from utils import notify_in_discord


def get_driver() -> WebDriver:
    """
    Create driver and fulfill required options
    """

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--use-fake-ui-for-media-stream')
    options.add_experimental_option('prefs', {
        'credentials_enable_service': False,
        'profile.default_content_setting_values.media_stream_mic': 1,
        'profile.default_content_setting_values.media_stream_camera': 1,
        'profile.default_content_setting_values.geolocation': 1,
        'profile.default_content_setting_values.notifications': 1,
        'profile': {
            'password_manager_enabled': False
        }
    })
    options.add_argument('--no-sandbox')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])

    if settings['mute_audio']:
        options.add_argument("--mute-audio")
    if settings['headless']:
        options.add_argument('--headless')
        print("Enabled headless mode")

    service = webdriver.ChromeService(
        executable_path=settings['driver_path'],
    )

    return webdriver.Chrome(options=options, service=service)


def get_element(
        driver: WebDriver,
        value: str,
        timeout: int,
        by: str = By.CSS_SELECTOR,
        raise_ex: bool = True,
) -> Optional[WebElement]:
    """
    Advanced functionality to find element in page.

    :param driver: WebDriver
    :param value: value to find. Used in driver.find_element(by, value)
    :param timeout: Max time to wait for element
    :param by: by what to find element. Used in driver.find_element(by, value)
    :param raise_ex: If it needed to raise exception when elem is not found.
    :return: founded WebElement
    """
    try:
        element_present = expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, value))
        WebDriverWait(driver, timeout).until(element_present)
    except exceptions.TimeoutException:
        if raise_ex:
            notify_in_discord("Exception", f"Timeout: {value}")
            raise ValueError(f"Timeout: {value}")
        else:
            return None

    return driver.find_element(by, value)


def log_in(driver: WebDriver):
    """
    Open https://teams.microsoft.com and log in
    """

    driver.get("https://teams.microsoft.com")

    # enter email
    email_field = get_element(driver, "input[type='email']", 15)
    email_field.send_keys(settings['email'])
    email_field.send_keys(Keys.ENTER)

    # enter password
    password_field = get_element(driver, "input[type='password']", 5)
    password_field.send_keys(settings['password'])
    password_field.send_keys(Keys.ENTER)

    # "keep logged in" message
    keep_logged_in_button_no = get_element(driver, "#idBtn_Back", 5)
    keep_logged_in_button_no.click()

    # use_web_instead = get_element(driver, ".use-app-lnk", 5, raise_ex=False)
    # if use_web_instead is not None:
    #     use_web_instead.click()

    print("Logged in")
    notify_in_discord("Log in", "Success")

    # wait for main page loaded
    print("Waiting for correct page...", end='')
    time.sleep(10)
    wait_for_main_page_is_loaded(driver)
    print("\rMain page loaded")


def wait_for_main_page_is_loaded(driver: WebDriver):
    try:
        get_element(driver, "#teams-app-bar", 50)
    except ValueError:
        notify_in_discord("Exception", "Can't load main page")
        raise ValueError("Can't load main page")


def filter_allowed_teams(team_elements: Iterable[WebElement]) -> Iterable[WebElement]:
    """
    Get rid of needless Teams. Return good Teams as generator.

    If settings['white_list'] is not empty:
        1) Find every Team that matches settings['white_list']
        2) From this set delete every Team that matches settings['black_list']
    Else:
        1) Get all Teams that not matches settings['black_list']

    This function uses title of Team as its identifier.
    """

    white_list = set(settings['white_list'])
    black_list = set(settings['black_list'])

    if white_list:  # white list is prioritised if exists
        for team_elem in team_elements:
            title = Team.get_team_title_by_elem(team_elem)
            if title in white_list and title not in black_list:
                yield team_elem
    elif black_list:  # if only black_list appear, uses it
        for team_elem in team_elements:
            title = Team.get_team_title_by_elem(team_elem)
            if title not in black_list:
                yield team_elem
    else:  # else no limitations
        for team_elem in team_elements:
            yield team_elem


def get_teams(driver: WebDriver) -> list[Team]:
    """
    Search for all Teams on main page. Ignores hidden teams.
    """
    # scroll_page(driver)
    unhidden_teams_block = driver.find_element(By.CSS_SELECTOR, "#favorite-teams-panel")
    team_elements = unhidden_teams_block.find_elements(By.CSS_SELECTOR, ".team-card")

    conn = connect()
    team_rows = {team_row.title: team_row for team_row in get_all_teams(conn)}
    conn.close()

    teams = [Team.parse_team(elem) for elem in filter_allowed_teams(team_elements)]
    for team in teams:
        if team.title in team_rows:
            team_row: TeamRow = team_rows[team.title]
            team.link = team_row.link
            team.id = team_row.id

    return teams


def handle_pre_meeting_window(driver: WebDriver):
    """
    Turn off microphone and camera and join meeting.

    You should be on pre-meeting page
    """

    # checkout iframe
    iframe = get_element(driver, 'iframe', 20, by=By.TAG_NAME)
    driver.switch_to.frame(iframe)

    # turn off microphone
    mic_checkbox = get_element(driver, "div[data-tid='toggle-mute']", 40)
    if mic_checkbox.get_attribute("aria-checked") == "true":
        mic_checkbox.click()

    # turn off camera
    camera_checkbox = get_element(driver, "div[data-tid='toggle-video']", 2)
    if camera_checkbox.get_attribute("aria-checked") == "true":
        camera_checkbox.click()

    time.sleep(1)

    # join meeting
    join_button = get_element(driver, "button[data-tid='prejoin-join-button']", 2)
    join_button.click()

    # back to main document
    driver.switch_to.default_content()


def handle_meeting(driver: WebDriver):
    """
    Do some stuff to control meeting
    """

    # store max number of attenders recorded in this meeting
    max_attenders = 0

    # instant leaving if this value of attenders
    min_attenders = settings["min_attenders"]

    # attenders threshold
    th1 = settings["attenders_threshold"]  # leave if *leaving_timer* seconds of this
    th2 = min(0.5, th1)  # or instant leaving if this threshold

    # number of attenders to reach to be able to leave.
    # if this value won't be reached, you don't leave.
    ia = 15

    leaving_timer = 0  # seconds to leave if (1 - th1) * 100% attenders have leaved
    started_leaving = False  # if leaving_timer started

    check_interval = 5  # time between two leaving checks

    # checkout iframe
    iframe = get_element(driver, 'iframe', 20, by=By.TAG_NAME)
    driver.switch_to.frame(iframe)

    def get_number_of_members() -> int:
        try:
            number_of_members_field = \
                driver.find_element(By.CSS_SELECTOR, "[data-tid='roster-button-tile']")
        except Exception:
            return 1
        return int(number_of_members_field.text)

    def leave_meeting():
        hangup_button = driver.find_element(By.CSS_SELECTOR, "#hangup-button")
        hangup_button.click()

    def need_to_leave() -> bool:
        nonlocal max_attenders, started_leaving, leaving_timer

        n = get_number_of_members()
        max_attenders = max(n, max_attenders)
        if max_attenders >= ia:
            if n < min_attenders:
                # instant leaving
                return True
            th_now = n / max_attenders
            if th_now <= th2:
                # instant leaving
                return True
            if started_leaving or th_now <= th1:
                if not started_leaving:
                    leaving_timer += check_interval
                    started_leaving = True
                leaving_timer -= check_interval
                if leaving_timer <= check_interval:
                    if leaving_timer > 0:
                        time.sleep(leaving_timer)
                    return True
        return False

    while True:
        if need_to_leave():
            leave_meeting()
            break
        time.sleep(check_interval)

    # back to main document
    driver.switch_to.default_content()


def check_teams(
        driver: WebDriver,
        teams: list[Team],
        last_team: Optional[Team] = None,
) -> Optional[Team]:
    """
    Check every team for active meeting. Also, collect link of every Team
    if it doesn't exist.

    :return current active Team, else last_team
    """
    wait = WebDriverWait(driver, 10)
    main_page_url = driver.current_url
    original_window = driver.current_window_handle

    conn = connect()

    def go_to_team_page(team: Team):
        if team.link:
            driver.get(team.link)
            wait_for_main_page_is_loaded(driver)
            # approve_team(conn, team.id)
        else:
            driver.get(main_page_url)
            wait_for_main_page_is_loaded(driver)
            team.update_elem(driver)
            team.elem.click()
            time.sleep(2)
            team.link = driver.current_url
            team.id = insert(conn, team.title, team.link)

    for team in teams:
        if team == last_team:
            continue
        driver.switch_to.new_window('tab')
        wait.until(expected_conditions.number_of_windows_to_be(2))
        go_to_team_page(team)

        active_channel = team.get_channel_with_meeting(driver)
        if active_channel:
            # open pre-joining window
            active_channel.elem.click()
            try:
                join_meeting_button = get_element(driver, "calling-join-button > button", 5)
            except ValueError:
                files_tab = driver.find_element(By.CSS_SELECTOR, "a[data-tid='FileBrowserTabApp']")
                files_tab.click()
                time.sleep(1)
                publications_tab = driver.find_element(By.CSS_SELECTOR, "a[data-tid='conversations']")
                publications_tab.click()
                join_meeting_button = get_element(driver, "calling-join-button > button", 10)

            print(f"Joining Team: \"{team.title}\"")
            join_meeting_button.click()
            time.sleep(2)

            handle_pre_meeting_window(driver)
            notify_in_discord("Join meeting", f"Team: {team.title}")
            handle_meeting(driver)
            print("Leave meeting")
            notify_in_discord("Leave meeting", f"Team: {team.title}")
            time.sleep(3)
            last_team = team

        driver.close()
        driver.switch_to.window(original_window)

    conn.close()
    return last_team


def main(driver: WebDriver):
    log_in(driver)
    teams = get_teams(driver)

    pause = settings["meeting_check_interval"]
    last_team: Optional[Team] = None
    while True:
        last_team = check_teams(driver, teams, last_team)
        time.sleep(pause)


if __name__ == '__main__':
    driver_ = get_driver()
    exc: Optional[Exception] = None
    try:
        main(driver_)
    except Exception as e:
        exc = e
    finally:
        driver_.quit()
        print("Finished")
        if exc:
            notify_in_discord("Finished", f"Exception raised")
        else:
            notify_in_discord("Finished", "Success")
