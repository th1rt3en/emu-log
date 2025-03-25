import json
import pandas as pd

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Add your service account credentials file
creds = Credentials.from_service_account_file('service_account.json', scopes=SCOPES)

# The ID and range of the spreadsheet
GROUP_NAMES = ["Moose", "Kangaroo", "Zebra", "Llama"]
SPREADSHEET_ID = '1zGgTAiwAPSxYTp6iplCasRzp4POD1AALpgnYcHmxu2E'

# Build the service
service = build('sheets', 'v4', credentials=creds)

for group in GROUP_NAMES:
    RANGE_NAME = f'Initial Stage ({group})!D3:J'  # Adjust the range as needed

    # Call the Sheets API to get the cell values and hyperlinks
    result = service.spreadsheets().get(
        spreadsheetId=SPREADSHEET_ID,
        ranges=RANGE_NAME,
        fields="sheets/data/rowData/values(userEnteredValue,hyperlink)"
    ).execute()

    sheets = result.get('sheets', [])
    matches = []

    if not sheets:
        print(f'No data found for group {group}.')
    else:
        for sheet in sheets:
            data = sheet.get('data', [])
            for datum in data:
                row_data = datum.get('rowData', [])
                for row in row_data:
                    values = row.get('values', [])
                    match = {
                        "match_id": values[0].get('userEnteredValue', {}).get('stringValue', None),
                        "match_url": values[0].get('hyperlink', 'No hyperlink'),
                        "player1": values[1].get('userEnteredValue', {}).get('stringValue', None),
                        "player1_score": values[2].get('userEnteredValue', {}).get('numberValue', None),
                        "player2_score": values[3].get('userEnteredValue', {}).get('numberValue', None),
                        "player2": values[4].get('userEnteredValue', {}).get('stringValue', None),
                    }
                    try:
                        match["number_of_turns"] = values[5].get('userEnteredValue', {}).get('numberValue', None)
                    except IndexError:
                        match["number_of_turns"] = None
                    try:
                        match["map"] = values[6].get('userEnteredValue', {}).get('stringValue', None)
                    except IndexError:
                        match["map"] = None
                    matches.append(match)

    pd.DataFrame(matches).to_csv(f"{group}.csv", index=False)