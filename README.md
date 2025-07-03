# Facebook Ad Scraper

This project contains a simple scraper for the Facebook Ad Library.

## Proxy Configuration

Configure an HTTP or HTTPS proxy for outbound requests by setting the following
environment variables before running the scraper:

- `PROXY_HTTP` – HTTP proxy URL (for example `http://user:pass@host:port`)
- `PROXY_HTTPS` – HTTPS proxy URL

If these variables are not set, requests will be made without a proxy.
