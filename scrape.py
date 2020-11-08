import requests
import argparse
import sys
import os
import json
import pickle

_DEFAULT_FILTER = {
    "min_rating": "4"
}
_VIVINO_URL = "https://www.vivino.com/api/explore/explore"
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0"}
_MATCHES_PER_PAGE = 100

_OUTPUT_FILE = "wines.pickle"
_DOWNLOAD_LABEL_SIZE = "label_medium"
_LABELS_OUTPUT_DIR = "labels"

parser = argparse.ArgumentParser()
parser.add_argument('--filter_json',
                    dest='filter_json',
                    type=str,
                    help='the path to filter json file')
parser.add_argument('--download_labels', 
                    dest='download_labels', 
                    action='store_true',
                    help="downloads wine labels if specified")
args = parser.parse_args()

if args.filter_json and not os.path.isfile(args.filter_json):
    print(f"The specified filter json file {args.filter_json} doesnt exist")
    sys.exit()

def scrape():
    # load filter from json file given as argument
    if args.filter_json:
        with open(args.filter_json) as f:
            params = json.load(f)
    else:
        params = _DEFAULT_FILTER

    # use pickle if exists
    if os.path.isfile(_OUTPUT_FILE):
        wines = pickle.load(open(_OUTPUT_FILE, "rb"))
    else:
        unique_wines = set()
        page = 1
        total_pages = 1
        wines = []

        while page <= total_pages:
            try:
                response = requests.get(
                    _VIVINO_URL,
                    params = {"page": f"{page}", **params},
                    headers= _HEADERS
                )
                records_matched = response.json()["explore_vintage"]["records_matched"]
                total_pages = records_matched // _MATCHES_PER_PAGE + 1
                new_wines = [wine for wine in response.json()["explore_vintage"]["matches"] if wine["vintage"]["id"] not in unique_wines]
                wines.extend(new_wines)
                unique_wines.update([wine["vintage"]["id"] for wine in new_wines])
            except:
                page += 1
                continue

            print(f"Scraped page {page} of {total_pages}")
            page += 1

        pickle.dump(wines, open(_OUTPUT_FILE, "wb"))

    # download wine label images
    if args.download_labels:
        wines_with_labels = [wine for wine in wines if wine["vintage"]["image"]["variations"].get(_DOWNLOAD_LABEL_SIZE, None) is not None]
        for i, wine in enumerate(wines_with_labels):
            file_name = f"{_LABELS_OUTPUT_DIR}/{wine['vintage']['id']}.png"
            if os.path.isfile(file_name):
                print(f"Skipping already downloaded label {file_name}")
            else:
                url = f"http:{wine['vintage']['image']['variations'][_DOWNLOAD_LABEL_SIZE]}"
                try:
                    response = requests.get(url)
                except:
                    print(f"Exception while downloading {url}")
                    continue
                if response.status_code == 200:
                    with open(file_name, 'wb') as f:
                        f.write(response.content)
                print(f"Downloaded wine label {i} of {len(wines_with_labels)}")


if __name__ == "__main__":
    scrape()