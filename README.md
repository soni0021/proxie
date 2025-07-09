# Proxy Scrapper Example

This project demonstrates how to use the Proxy-List-Scrapper package to fetch free proxies from various sources and use them for web scraping with round-robin rotation.

## Installation

1. Make sure you have Python 3.x installed
2. Install the required packages:
   ```
   pip3 install Proxy-List-Scrapper beautifulsoup4 pandas matplotlib
   ```

## Usage

### Basic Proxy Scraping
Run the basic example to fetch proxies from the SSL category:
```
python3 proxy_scraper_test.py
```

### Advanced Proxy Scraping
Run the advanced example to fetch proxies from multiple categories and save them to files:
```
python3 proxy_scraper_advanced.py
```

### Testing Proxies
Test a random proxy from one of the proxy files:
```
python3 proxy_usage_example.py
```

Or specify a specific proxy file:
```
python3 proxy_usage_example.py google_proxies.txt
```

### Web Scraping with Proxy Rotation
Use the website scraper with round-robin proxy rotation:
```
python3 scrape_example.py
```

For more control, use the full scraper with command-line arguments:
```
python3 website_scraper.py https://example.com --pages 10 --delay-min 2 --delay-max 5
```

### Wikipedia Scraping
We provide several methods to scrape Wikipedia data with and without proxies:

#### Country Data Scraper with Proxy Rotation
```
python3 wiki_country_scraper.py --count 5 --proxies
```

#### Simple Direct Wikipedia Scraper (No Proxies)
```
python3 wiki_simple_scraper.py --count 5
```

#### Table Scraper for Structured Data
```
python3 wiki_table_scraper.py
```

You can also specify a different Wikipedia table URL:
```
python3 wiki_table_scraper.py --url "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)"
```

### Round-Robin Proxy Demo
Demonstrate scraping the same countries multiple times, each time with a different proxy via round-robin rotation:

```
python3 country_proxy_demo.py
```

You can specify more iterations:
```
python3 country_proxy_demo.py --iterations 10
```

### Proxy Performance Analysis
After running the country_proxy_demo.py script, you can analyze which proxies performed best:

```
python3 proxy_performance.py
```

This will generate:
- A report showing the best and worst performing proxies
- A CSV file with detailed proxy performance data
- A visualization of the top 10 proxies by success rate

### Proxy Manager Tool
The proxy manager provides a command-line interface for working with proxies:

Test a single proxy:
```
python3 proxy_manager.py test 123.456.789.012:8080
```

Test multiple proxies from a file:
```
python3 proxy_manager.py test-file ssl_proxies.txt --count 5 --random
```

Test proxy rotation:
```
python3 proxy_manager.py rotate --count 5
```

Fetch a URL using rotating proxies:
```
python3 proxy_manager.py fetch https://httpbin.org/ip --count 3
```

Save working proxies to a file:
```
python3 proxy_manager.py test-file ssl_proxies.txt --count 20 --save working_proxies.txt
```

## Components

### Proxy Scraping
- `proxy_scraper_test.py`: Basic proxy scraping from a single source
- `proxy_scraper_advanced.py`: Advanced proxy scraping from multiple sources

### Proxy Rotation
- `proxy_rotator.py`: A class that implements round-robin rotation of proxies with failure tracking
- `proxy_usage_example.py`: Example of using a proxy with the requests library
- `proxy_manager.py`: Command-line tool for testing and using proxies

### Web Scraping
- `website_scraper.py`: A web scraper that uses rotating proxies
- `scrape_example.py`: Simple example of scraping a website with proxy rotation

### Wikipedia Scraping
- `wiki_country_scraper.py`: Scrape country data from Wikipedia with proxy rotation option
- `wiki_simple_scraper.py`: Direct scraping of Wikipedia without proxies
- `wiki_table_scraper.py`: Extract structured data from Wikipedia tables

### Advanced Demonstrations
- `country_proxy_demo.py`: Demo that scrapes countries multiple times using different proxies each time
- `proxy_performance.py`: Analyzes which proxies perform best based on the demo results

## Available Proxy Categories

- SSL = 'https://www.sslproxies.org/'
- GOOGLE = 'https://www.google-proxy.net/'
- ANANY = 'https://free-proxy-list.net/anonymous-proxy.html'
- UK = 'https://free-proxy-list.net/uk-proxy.html'
- US = 'https://www.us-proxy.org/'
- NEW = 'https://free-proxy-list.net/'
- SPYS_ME = 'http://spys.me/proxy.txt'
- PROXYSCRAPE = 'https://api.proxyscrape.com/?request=getproxies&proxytype=all&country=all&ssl=all&anonymity=all'
- PROXYNOVA = 'https://www.proxynova.com/proxy-server-list/'
- PROXYLIST_DOWNLOAD_HTTP = 'https://www.proxy-list.download/HTTP'
- PROXYLIST_DOWNLOAD_HTTPS = 'https://www.proxy-list.download/HTTPS'
- PROXYLIST_DOWNLOAD_SOCKS4 = 'https://www.proxy-list.download/SOCKS4'
- PROXYLIST_DOWNLOAD_SOCKS5 = 'https://www.proxy-list.download/SOCKS5'
- ALL = 'ALL'

## How Round-Robin Proxy Rotation Works

The proxy rotation system works as follows:

1. Proxies are loaded from files and stored in a queue
2. For each request, the system takes the next proxy from the front of the queue
3. After using a proxy, it's moved to the back of the queue (round-robin)
4. Failed proxies are tracked and potentially removed if they fail too often
5. This ensures the load is distributed across all available proxies

## Handling Proxy Failures

Our system provides several mechanisms to handle proxy failures:

1. **Failure Tracking**: Each proxy's success and failure rates are tracked
2. **Consecutive Failures**: Proxies that fail too many times in a row are removed
3. **Success Rate Threshold**: Proxies with a low success rate are dropped
4. **Fallback to Direct Connection**: If all proxies fail, the system can fall back to a direct connection

## Best Practices for Web Scraping

1. Respect the website's robots.txt file
2. Add delays between requests to avoid overloading servers
3. Use a descriptive User-Agent so websites know who is scraping
4. Implement error handling for failed requests
5. Be mindful of the website's terms of service

## Output Files

The scrapers produce several types of output files:

### Proxy Lists
- `ssl_proxies.txt`, `google_proxies.txt`, etc.: Lists of proxies from different sources
- `working_proxies.txt`: Verified working proxies (if you use the `--save` option)

### Scraped Data
- `countries_data_*.json`: Country information scraped from Wikipedia
- `country_table_data.json`: Structured table data from Wikipedia
- `country_table_data.csv`: CSV version of the table data

### Analysis Results
- `country_proxy_demo_*.json`: Results of the proxy rotation demo
- `proxy_performance.csv`: Detailed proxy performance statistics
- `proxy_performance_chart.png`: Visualization of top-performing proxies

## Credits

This example uses the [Proxy-List-Scrapper](https://github.com/narkhedesam/Proxy-List-Scrapper) package by Sameer Narkhede. 