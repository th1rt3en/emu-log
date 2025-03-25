import re
import pandas as pd

from time import sleep
from io import StringIO
from playwright.sync_api import sync_playwright


def login(page):
    # page.goto("https://boardgamearena.com/gamereview?table=625633595")
    # page.locator(".bga-account-manager-form__step1 > div:nth-child(2) > form:nth-child(1) > div:nth-child(2) > div:nth-child(1) > input:nth-child(2)").fill(email)
    # page.locator("div.z-0:nth-child(3) > div:nth-child(1) > a:nth-child(1)").click()
    # page.locator(".bga-account-manager-form__password-field > div:nth-child(1) > input:nth-child(1)").fill(pwd)
    # page.locator("form.space-y-4 > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > a:nth-child(1)").click()
    # sleep(2)
    # page.get_by_text("Let's play!").last.click()
    # page.wait_for_load_state('networkidle') 

    # perform manual login for consistency
    page.goto("https://boardgamearena.com/gamereview?table=625633595")
    input("Press enter after logging in")


GROUP_NAMES = ["Moose", "Kangaroo", "Zebra", "Llama"]
matches_df = []
for group in GROUP_NAMES:
    matches_df.append(pd.read_csv(f"{group}.csv"))

matches_df = pd.concat(matches_df)
print(matches_df)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    login(page)

    with open("log.txt", "w") as log:
        for _, match_info in matches_df.iterrows():
            match_id = match_info["match_id"]
            match_url = match_info["match_url"]
            if match_url.startswith("https://"):
                player1 = match_info["player1"]
                player2 = match_info["player2"]
                player1_score = int(match_info["player1_score"])
                player2_score = int(match_info["player2_score"])
                try:
                    map = re.findall(r"\((\w+)\)", match_info["map"])[0]
                except Exception:
                    log.writelines(f"Map not found for {match_url}\n")
                    map = None
                try:
                    number_of_turns = int(match_info["number_of_turns"])
                except ValueError:
                    number_of_turns = None

                log.writelines(f"checking {match_url}\n")
                page.goto(match_url)
                table = page.locator("#player_stats")
                df = pd.read_html(StringIO(table.inner_html()))[0]
                df.rename(columns={"Unnamed: 0": "stat"}, inplace=True)

                starting_position = df[df["stat"] == "Starting position in first round"].iloc[0].values.tolist()[1]

                if starting_position == "First player":
                    actual_player1, actual_player2 = df.columns.values.tolist()[1:]
                else:
                    actual_player2, actual_player1 = df.columns.values.tolist()[1:]
                if actual_player1 != player1 or actual_player2 != player2:
                    log.writelines(f"Player names do not match for {match_url}\n")
                    log.writelines(f"Expected: {player1}, {player2}\n")
                    log.writelines(f"Actual: {actual_player1}, {actual_player2}\n")

                if starting_position == "First player":
                    actual_player1_score = int(re.findall(r"\((\d+)\)", df[df["stat"] == "Game result"].iloc[0].values.tolist()[1])[0])
                    actual_player2_score = int(re.findall(r"\((\d+)\)", df[df["stat"] == "Game result"].iloc[0].values.tolist()[2])[0])
                else:
                    actual_player2_score = int(re.findall(r"\((\d+)\)", df[df["stat"] == "Game result"].iloc[0].values.tolist()[1])[0])
                    actual_player1_score = int(re.findall(r"\((\d+)\)", df[df["stat"] == "Game result"].iloc[0].values.tolist()[2])[0])
                if actual_player1_score != player1_score or actual_player2_score != player2_score:
                    log.writelines(f"Player scores do not match for {match_url}\n")
                    log.writelines(f"Expected: {player1_score}, {player2_score}\n")
                    log.writelines(f"Actual: {actual_player1_score}, {actual_player2_score}\n")

                try:
                    actual_map = re.findall(r"(\w+)\:", df[df["stat"] == "Map"].iloc[0].values.tolist()[1])[0]
                except IndexError:
                    print(match_url)
                if actual_map != map:
                    log.writelines(f"Map does not match for {match_url}\n")
                    log.writelines(f"Expected: {map}\n")
                    log.writelines(f"Actual: {actual_map}\n")

                actual_number_of_turns = min(int(x) for x in df[df["stat"] == "Number of turns"].iloc[0].values.tolist()[1:])
                if actual_number_of_turns != number_of_turns and number_of_turns is not None:
                    log.writelines(f"Number of turns does not match for {match_url}\n")
                    log.writelines(f"Expected: {number_of_turns}\n")
                    log.writelines(f"Actual: {actual_number_of_turns}\n")  
                
                log.writelines(f"Match verified {match_id}\n")

        browser.close()