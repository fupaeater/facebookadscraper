# Facebook Ad Scraper

This project contains a simple scraper for the Facebook Ad Library.

## Proxy Configuration

The scraper can route requests through a proxy. There are two ways to provide
the proxy details:

1. **Environment variables** – set `PROXY_HTTP` and `PROXY_HTTPS` before running
   the script. These override any values in the code.
2. **Edit the script** – open `facebook_ad_scraper.py` and set
   `DEFAULT_PROXY_HTTP` and `DEFAULT_PROXY_HTTPS` near the top of the file.

When either method provides values, requests made by
`facebook_ad_scraper.py` will use them for outbound connections.
