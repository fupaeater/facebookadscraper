from datetime import datetime

from facebook_ad_scraper.facebook_ad_scraper import FacebookAdScraper


def main():
    search_terms = ["Shop Now","Sale","Free Shipping","50% off","Limited stock", "Limited Time","Buy now","Order now", "Get Yours Now", "Only today", "Claim yours","30% off", "60% off", "Claim yours now", "Free worldwide shipping", "Get it now", "Get yours", "Grab yours now", "Click here", "Order link"]

    #["30% off", "60% off", "Claim yours now", "Free worldwide shipping", "Get it now", "Get yours", "Grab yours now", "Click here", "Order link"]
    #["Shop Now","Sale","Free Shipping","50% off","Limited Time","Buy now","Order now", "Get Yours Now", "Only today", "Claim yours"]

    # csv file name with current time
    csv_file = f"output/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"

    fb = FacebookAdScraper(search_terms, csv_file)
    fb.main()


if __name__ == '__main__':
    main()
