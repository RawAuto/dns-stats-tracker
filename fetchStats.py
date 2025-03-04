#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import getpass
import csv
import sys
import os

# Constants
RAWDATAURL = "https://dashboard.opendns.com"
LOGINURL = "https://login.opendns.com/?source=dashboard"

def usage():
    print("Usage: python fetchstats.py <username> <network_id> <YYYY-MM-DD> [<YYYY-MM-DD>] <output_file>")
    sys.exit(1)

def date_check(date_str):
    if not date_str or len(date_str) != 10 or date_str[4] != '-' or date_str[7] != '-':
        print("Error: dates must be in the YYYY-MM-DD form")
        sys.exit(2)

def main():
    if len(sys.argv) not in [5, 6]:
        usage()

    USERNAME = sys.argv[1]
    NETWORK_ID = sys.argv[2]
    date_check(sys.argv[3])
    if len(sys.argv) == 5:
        DATE = sys.argv[3]
        OUTPUT_FILE = sys.argv[4]
    else:
        date_check(sys.argv[4])
        DATE = f"{sys.argv[3]}to{sys.argv[4]}"
        OUTPUT_FILE = sys.argv[5]

    # Prompt for password
    PASSWORD = getpass.getpass(f"Password for {USERNAME}: ")

    # Create a session to handle cookies
    session = requests.Session()

    # Get the signin page's form token
    response = session.get(LOGINURL)
    soup = BeautifulSoup(response.text, 'html.parser')
    formtoken = soup.find('input', {'name': 'formtoken'})['value']
    print(f"Form token: {formtoken}")

    # Sign into OpenDNS and follow the redirect
    login_data = {
        'formtoken': formtoken,
        'username': USERNAME,
        'password': PASSWORD,
        'sign_in_submit': 'foo'
    }
    login_response = session.post(LOGINURL, data=login_data, allow_redirects=True)

    # Check if we're successfully redirected to the dashboard
    if 'dashboard' in login_response.url:
        print("Login successful!")
    else:
        print("Login failed. Check username and password.")
        sys.exit(2)

    # Fetch pages of Top Domains
    page = 1
    all_data = []

    while True:
        print(f"Fetching page {page}...")
        csv_url = f"{RAWDATAURL}/stats/{NETWORK_ID}/topdomains/{DATE}/page{page}.csv"
        response = session.get(csv_url)

        if response.status_code != 200 or 'DOCTYPE' in response.text:
            print(f"No more data at page {page}.")
            break

        lines = response.text.strip().split('\n')
        if page == 1:
            if not lines:
                print(f"You cannot access {NETWORK_ID}")
                sys.exit(2)
            heading = lines[0]
            all_data.append(heading.split(','))
            data_lines = lines[1:]
        else:
            data_lines = lines[1:]

        if not data_lines:
            print(f"No more data at page {page}.")
            break

        for line in data_lines:
            all_data.append(line.split(','))

        page += 1

    # Write to CSV file
    with open(OUTPUT_FILE, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(all_data)

    print("Finished fetching all pages.")

if __name__ == "__main__":
    main()
