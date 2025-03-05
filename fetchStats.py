#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import getpass
import csv
import sys

# Constants
raw_data_url = "https://dashboard.opendns.com"
login_url = "https://login.opendns.com/?source=dashboard"


def usage():
    print("Usage: python fetchstats.py <username> <network_id> <YYYY-MM-DD> [<YYYY-MM-DD>] <output_file>")
    sys.exit(1)


def date_check(date_str):
    if not date_str or len(date_str) != 10 or date_str[4] != '-' or date_str[7] != '-':
        print("Error: dates must be in the YYYY-MM-DD form")
        sys.exit(2)


def fetch_form_token(session):
    response = session.get(login_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.find('input', {'name': 'formtoken'})['value']


def login(session, username, password, formtoken):
    login_data = {
        'formtoken': formtoken,
        'username': username,
        'password': password,
        'sign_in_submit': 'foo'
    }
    response = session.post(login_url, data=login_data, allow_redirects=True)
    return 'dashboard' in response.url


def fetch_data(session, network_id, date, page):
    csv_url = f"{raw_data_url}/stats/{network_id}/topdomains/{date}/page{page}.csv"
    response = session.get(csv_url)
    return response


def write_to_csv(output_file, all_data):
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(all_data)


def main():
    if len(sys.argv) not in [5, 6]:
        usage()

    username = sys.argv[1]
    network_id = sys.argv[2]
    date_check(sys.argv[3])
    if len(sys.argv) == 5:
        date = sys.argv[3]
        output_file = sys.argv[4]
    else:
        date_check(sys.argv[4])
        date = f"{sys.argv[3]}to{sys.argv[4]}"
        output_file = sys.argv[5]

    password = getpass.getpass(f"Password for {username}: ")

    session = requests.Session()
    form_token = fetch_form_token(session)
    print(f"Form token: {form_token}")

    if not login(session, username, password, form_token):
        print("Login failed. Check username and password.")
        sys.exit(2)

    print("Login successful!")

    page = 1
    all_data = []

    while True:
        print(f"Fetching page {page}...")
        response = fetch_data(session, network_id, date, page)

        if response.status_code != 200 or 'DOCTYPE' in response.text:
            print(f"No more data at page {page}.")
            break

        lines = response.text.strip().split('\n')
        if page == 1:
            if not lines:
                print(f"You cannot access {network_id}")
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

    write_to_csv(output_file, all_data)
    print("Finished fetching all pages.")


if __name__ == "__main__":
    main()
