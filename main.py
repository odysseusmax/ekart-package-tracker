import os
import json
import time
from pathlib import Path
import concurrent.futures

import requests
from bs4 import BeautifulSoup
from playsound import playsound


TRACKING_DETAILS_FOLDER = Path(".trackingfiles/")
SLEEP_FOR = 60 * 15
CANCELLED = False
PATH_TO_NOTIFICATION_AUDIO = "notification.wav"


def find_difference(a, b):
    return [x for x in a if x not in b]


def convert(table):
    thead = table.thead
    tbody = table.tbody
    fields = [th.string for th in thead.find_all("th")]
    return [
        {
            key: value
            for key, value in zip(fields, (td.string for td in tr.find_all("td")))
        }
        for tr in tbody.find_all("tr")
    ]


def track(tracking_id):
    print("started for tracking id", tracking_id)
    tracking_file_details = TRACKING_DETAILS_FOLDER.joinpath(f"{tracking_id}.json")
    tracking_details = []
    if tracking_file_details.exists():
        with open(tracking_file_details, "r") as fp:
            tracking_details = json.load(fp)

    last_at = time.time() - SLEEP_FOR - 1
    while not CANCELLED:
        if time.time() - last_at < SLEEP_FOR:
            time.sleep(1)
            continue

        url = f"https://portal.ekartlogistics.com/track/{tracking_id}/"
        req = requests.get(url)
        soup = BeautifulSoup(req.text, "html.parser")
        table = soup.find_all("table")[1]
        new_details = convert(table)
        diff = find_difference(new_details, tracking_details)
        if diff:
            print("Change detected for ", tracking_id)
            for diff_ in diff:
                playsound(PATH_TO_NOTIFICATION_AUDIO)
                print(diff_)

            tracking_details = new_details
            with open(tracking_file_details, "w") as fp:
                json.dump(new_details, fp)
        last_at = time.time()

    print("exiting")


def main():
    global CANCELLED
    tracking_ids = set(input("Enter tracking ids separated by space: ").split(" "))
    if not tracking_ids:
        return

    max_workers = min(15, len(tracking_ids))
    os.makedirs(TRACKING_DETAILS_FOLDER, exist_ok=True)
    executor = concurrent.futures.ThreadPoolExecutor(max_workers)
    futures = [executor.submit(track, tracking_id) for tracking_id in tracking_ids]
    try:
        while not all(future.done() for future in futures):
            time.sleep(0.5)

    except KeyboardInterrupt:
        CANCELLED = True
    finally:
        executor.shutdown(wait=False)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
