import csv
import json
import os
import random
import time
import re

import tldextract
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from .utils import extract_base_domain, create_session, utc_zone, cst_zone
from tenacity import retry, stop_after_attempt, wait_fixed

global_set = set()
# with open('proxies.txt', 'r') as file:
#     proxies = file.readlines()

class FacebookAdScraper:
    ads_url = "https://www.facebook.com/ads/library/async/search_ads/"
    query_parameters = {
        'q': '"shop now"',
        'count': 30,
        'active_status': 'active',
        'ad_type': 'all',
        'countries[0]': 'US',
        'publisher_platforms[0]': 'facebook',
        'publisher_platforms[1]': 'instagram',
        'start_date[min]': '2025-06-19',
        'start_date[max]': '2025-06-19',
        'media_type': 'video',
        'content_languages[0]': 'en',
        'search_type': 'keyword_exact_phrase'
    }
    # not logged in
    payload = '__a=1&lsd=AVreThNuNQ4'
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded',
        'cookie': 'wd=1462x1914; datr=J_AIZns_svZOGbHWBpByxavw',
        'origin': 'https://www.facebook.com',
        'pragma': 'no-cache',
        'referer': 'https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&q=shop%20now&search_type=keyword_unordered&media_type=all',
        'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'x-asbd-id': '129477',
        'x-fb-lsd': 'AVreThNuNQ4'
    }
    # logged in
    # payload = '__a=1&fb_dtsg=NAcP0XgX3hMNFYesm968TfTgrglmBVS9fSvDLChfA7IPl13YPVk_3hQ:41:1711854228' # __a and fb_dtsg required for logged in. __a and lsd required for not logged in
    # headers = {
    #     'authority': 'www.facebook.com',
    #     'accept': '*/*',
    #     'accept-language': 'en-US,en;q=0.9',
    #     'cache-control': 'no-cache',
    #     'content-type': 'application/x-www-form-urlencoded',
    #     'dpr': '1',
    #     'origin': 'https://www.facebook.com',
    #     'pragma': 'no-cache',
    #     'sec-ch-prefers-color-scheme': 'dark',
    #     'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    #     'sec-ch-ua-full-version-list': '"Not A(Brand";v="99.0.0.0", "Google Chrome";v="121.0.6167.189", "Chromium";v="121.0.6167.189"',
    #     'sec-ch-ua-mobile': '?0',
    #     'sec-ch-ua-model': '""',
    #     'sec-ch-ua-platform': '"Windows"',
    #     'sec-ch-ua-platform-version': '"15.0.0"',
    #     'sec-fetch-dest': 'empty',
    #     'sec-fetch-mode': 'cors',
    #     'sec-fetch-site': 'same-origin',
    #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    #     'viewport-width': '1688'
    # }

    # cookies = { # required for logged in
    #     'c_user': '100056190078747',
    #     'xs': '41%3AU65SoONT5M5jpg%3A2%3A1711854228%3A-1%3A7993'
    # }

    processed_urls = set()
    forward_cursor = None
    max_pages = 100

    def __init__(self, terms: list, csv_file: str):
        """
        Initializes the Facebook scraper with search terms
        :param terms: search terms to scrape
        :param csv_file: file name for csv
        """
        self.search_terms = terms
        self.csv_file = csv_file

    def main(self):
        """
        Submits workers for each search term in separate threads
        """
        print(f'Creating ads in file {self.csv_file}')
        with ThreadPoolExecutor(max_workers=len(self.search_terms)) as executor:
            for term in self.search_terms:
                executor.submit(self._fetch_and_extract_data_for_term, term)

    def _fetch_and_extract_data_for_term(self, term):
        local_extracted_data = []
        url_count = 1

        forward_cursor = None
        while url_count <= self.max_pages:
            print(f"Processing page {url_count} for term '{term}'")
            try:
                json_data = self.fetch_ads(search_term=term, new_cursor=forward_cursor)
                data_to_write = self._extract_data(json_data)
                file_exists = os.path.isfile(self.csv_file) and os.path.getsize(self.csv_file) > 0

                pages_found = 0
                with open(self.csv_file, mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)

                    if not file_exists:
                        writer.writerow(['ad_id', 'ad_url', 'creation_time', 'shop_name', 'shop_url'])

                    for row in data_to_write:
                        ad_creative_id, link_url, base_domain, page_name = row
                        # Write the row with URL and base domain
                        if link_url not in self.processed_urls:
                            pages_found += 1
                            base_domain = extract_base_domain(link_url)
                            row.append(base_domain)
                            writer.writerow(row)
                            local_extracted_data.append((link_url, base_domain))
                            self.processed_urls.add(link_url)

                print(f"New ad links found on page {url_count} for term '{term}' - {pages_found}")
                forward_cursor = json_data['payload'].get('forwardCursor')
                if not forward_cursor:
                    break
                url_count += 1

            except Exception as e:
                print(f"Error processing {term}: {str(e)}")
        print(f'finished ads in file {self.csv_file}')

    def fetch_ads(self, search_term, new_cursor=None, is_ads_count=False):
        """
        Fetches the ads from Facebook unofficial API
        :param url: modified url with cursor and search term
        :return: json data
        """
        # while True:
        params = self.query_parameters.copy()
        params['q'] = search_term
        if new_cursor:
            params['forward_cursor'] = new_cursor
        if is_ads_count:
            params.pop('start_date[min]', None)
            params.pop('media_type', None)
            params.pop('countries[0]', None)

        # small delay between requests to reduce chance of rate limiting
        time.sleep(random.uniform(1, 3))

        @retry(stop=stop_after_attempt(4), wait=wait_fixed(2), reraise=True)
        def req_ad():
            response = create_session().post(
                self.ads_url,
                params=params,
                headers=self.headers,
                data=self.payload,
                proxies={
                    'http': 'http://package-256469-country-us:bTYjLCJDrIppKckZ@proxy.soax.com:5000',
                    'https': 'http://package-256469-country-us:bTYjLCJDrIppKckZ@proxy.soax.com:5000'
                },
                timeout=10
            )
            if response.status_code != 200:
                print(f"Received status code {response.status_code}")
            return response

        try:
            response = req_ad()
        except:
            return {}
        response_text = response.text
        json_text = response_text[len('for (;;);'):]
        json_data = json.loads(json_text)
        if 'error' in json_data:
            description = json_data.get('errorDescription', {})
            if isinstance(description, dict) and description.get('__html'):
                clean_text = re.sub('<[^<]+?>', '', description['__html']).strip()
            else:
                clean_text = str(description)
            print(f"Error fetching ads for '{search_term}': {clean_text}")
            print('Sleeping for 60 seconds...')
            time.sleep(60)
            return {}
        return json_data

    @staticmethod
    def _extract_data(data):
        """
        Parse the ads info: creative id, website, ads page, and creation time
        :param data: response data from Facebook ads search API
        """
        extracted_data = []
        for group in data['payload']['results']:
            for item in group:
                snapshot = item.get('snapshot', {})
                if isinstance(snapshot, dict):
                    link_url = snapshot.get('link_url')
                    ad_creative_id = snapshot.get('ad_creative_id')
                    creation_time = snapshot.get('creation_time')
                    page_name = snapshot.get('page_name')
                    if creation_time:
                        utc_time = datetime.utcfromtimestamp(creation_time)
                        utc_time = utc_zone.localize(utc_time)
                        creation_time = utc_time.astimezone(cst_zone)

                    if link_url and ad_creative_id and creation_time and page_name:
                        extracted_domain = tldextract.extract(link_url).registered_domain
                        if extracted_domain in global_set:
                            continue
                        global_set.add(extracted_domain)
                        # print(link_url, ad_creative_id, creation_time.strftime('%Y-%m-%d %H:%M:%S %Z%z'), page_name)
                        extracted_data.append(
                            [ad_creative_id, link_url, creation_time.strftime('%Y-%m-%d %H:%M:%S %Z%z'), page_name])
        return extracted_data

    @staticmethod
    def load_random_proxy():
        """
        Load and return a random proxy from the proxies.txt file.
        """
        proxy = random.choice(proxies).strip()
        parts = proxy.split(':')

        if len(parts) < 3:
            raise ValueError("The proxy format is incorrect in the file.")

        host = parts[0]
        port = parts[1]
        credentials = ':'.join(parts[2:])

        formatted_proxy = f'http://{credentials}@{host}:{port}'

        return {'http': formatted_proxy, 'https': formatted_proxy}
