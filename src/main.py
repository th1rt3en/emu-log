import re
import pandas as pd

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


GROUP_NAMES = ["Kangaroo", "Llama", "Moose", "Zebra"]
matches_df = []
for group in GROUP_NAMES:
    df = pd.read_csv(f"{group}.csv")
    df["flock"] = group
    matches_df.append(df)

matches_df = pd.concat(matches_df)
print(matches_df)

game_stat = []
cards_stat = []


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    login(page)

    for _, match_info in matches_df.iterrows():
        match_url = match_info["match_url"]
        match_id = match_info["match_id"]
        if match_id <= "M111":
            continue
        if match_id >= "M211":
            break
        if not match_url.startswith("https://"):
            continue
        bga_match_id = re.findall(r"table=(\d+)", match_url)[0]
        match_log_url = f"https://boardgamearena.com/gamereview?table={bga_match_id}"
        print(f"checking {match_id}")
        page.goto(match_url)
        
        table = page.locator("#player_stats")
        df = pd.read_html(StringIO(table.inner_html()))[0]
        df.rename(columns={"Unnamed: 0": "stat"}, inplace=True)
        df = df.T
        new_columns = df.iloc[0]
        df = df[1:]
        df.columns = new_columns

        df["Game result"] = df["Game result"].apply(lambda x: re.findall(r"\d", x)[0])
        df.reset_index(inplace=True)
        df.drop(columns=["All stats"], inplace=True)
        df.rename(columns={"index": "player"}, inplace=True)
        df["match_id"] = match_id
        df["flock"] = match_info["flock"]
        winner = df[df["Game result"] == "1"]["player"].values[0]
        game_stat.append(df)

        page.goto(match_log_url)
        page.wait_for_load_state("networkidle")
        page.wait_for_load_state("domcontentloaded")
        for log in page.locator("#gamelogs > .gamelogreview").all():
            if "plays" in log.text_content() or "buys" in log.text_content():
                player = re.findall(r"^(.+) (plays|buys)", log.text_content())[0][0]
                card_string = re.findall(r"(plays|buys) (.*)", log.text_content())[0][1]
                if re.findall(r"and places it", card_string):
                    card_type = "animal"
                    if "from display" in card_string:
                        card_name = re.findall(r"(.+) from display", card_string)[0]
                        from_display = True
                    else:
                        card_name = re.findall(r"(.+) for (\d+)", card_string)[0][0]
                        from_display = False
                elif re.findall(r"a new conservation project", card_string):
                    if "from display" in card_string:
                        from_display = True
                    else:
                        from_display = False
                    card_type = "project"
                    card_name = re.findall(r"a new conservation project(.*): (.+)$", card_string)[0][1]
                else:
                    card_type = "sponsor"
                    if card_string.endswith("from display"):
                        card_name = card_string[:-12]
                        from_display = True
                    else:
                        card_name = card_string
                        from_display = False
                cards_stat.append({
                    "player": player, 
                    "card": card_name, 
                    "card_type": card_type,
                    "match_id": match_id, 
                    "flock": match_info["flock"],
                    "won": player == winner
                })

    browser.close()

# game_stat = pd.concat(game_stat)
# game_stat.to_csv("game_stat.csv", index=False)
cards_stat = pd.DataFrame(cards_stat)
cards_stat.to_csv("card_stat2.csv", index=False)
