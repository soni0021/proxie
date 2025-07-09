# 🚂 Indian Railway Scraper with Proxy Protection

A comprehensive and safe Indian Railway data scraper that uses proxy rotation to avoid IP bans and legal issues. This system provides multiple interfaces for scraping train data, schedules, and station information from Indian Railway websites.

## 🌟 Features

### 🔒 Safety & Legal Protection
- **Proxy Rotation**: Uses round-robin proxy rotation to avoid IP detection
- **Random Delays**: Implements random delays between requests (2-5 seconds)
- **Multiple Fallback URLs**: Tries different Indian Railway endpoints
- **Error Handling**: Comprehensive error handling with retry logic
- **Respectful Scraping**: Follows best practices to avoid overloading servers

### 📊 Data Collection
- **Train Search**: Find trains between any two stations
- **Train Schedules**: Get detailed timetables for specific trains
- **Station Information**: Get comprehensive station data and passing trains
- **Real-time Data**: Scrapes live data from official Indian Railway sources

### 🖥️ Multiple Interfaces
- **Command Line Interface**: User-friendly CLI with menus and prompts
- **Web Application**: Modern web interface with real-time updates
- **Python API**: Direct programmatic access to scraping functions

## 📁 File Structure

```
├── indian_railway_scraper.py    # Core scraper with proxy rotation
├── railway_interface.py         # Command-line interface
├── railway_web_app.py           # Flask web application
├── templates/
│   └── index.html              # Web interface template
├── *_proxies.txt               # Proxy files (from previous setup)
└── RAILWAY_README.md           # This documentation
```

## 🚀 Quick Start

### 1. Prerequisites

Make sure you have the required dependencies:

```bash
pip3 install requests beautifulsoup4 flask
```

### 2. Get Fresh Proxies

First, get some proxies for safe scraping:

```bash
python3 proxy_scraper_advanced.py
```

This will create several proxy files (`ssl_proxies.txt`, `google_proxies.txt`, etc.)

### 3. Choose Your Interface

#### Option A: Command Line Interface (Recommended for beginners)

```bash
python3 railway_interface.py
```

Features:
- 🔍 Interactive train search
- 📅 Train schedule lookup
- 🏢 Station information
- 📊 Session data management
- ⚙️ Proxy status monitoring

#### Option B: Web Application (Best user experience)

```bash
python3 railway_web_app.py
```

Then open your browser to: `http://localhost:5000`

Features:
- 🌐 Modern web interface
- 📱 Mobile-responsive design
- 🔄 Real-time scraping status
- 📊 Background processing
- 💾 Data export functionality

#### Option C: Direct Python Usage

```python
from indian_railway_scraper import IndianRailwayScraper

scraper = IndianRailwayScraper()

# Search trains
trains = scraper.search_trains("NDLS", "MMCT", "25-12-2024")

# Get train schedule
schedule = scraper.get_train_schedule("12951")

# Get station info
station_info = scraper.get_station_info("NDLS")
```

## 🎯 Usage Examples

### Train Search

Search for trains between New Delhi (NDLS) and Mumbai Central (MMCT):

```python
trains = scraper.search_trains("NDLS", "MMCT", "25-12-2024")
for train in trains:
    print(f"Train {train['train_number']}: {train['train_name']}")
    print(f"Departure: {train.get('departure_time', 'N/A')}")
    print(f"Arrival: {train.get('arrival_time', 'N/A')}")
```

### Train Schedule

Get detailed schedule for a specific train:

```python
schedule = scraper.get_train_schedule("12951")
if schedule:
    print(f"Schedule for Train {schedule['train_number']}:")
    for station in schedule['stations']:
        print(f"{station['station']} - Arr: {station.get('arrival', 'N/A')} Dep: {station.get('departure', 'N/A')}")
```

### Station Information

Get information about a railway station:

```python
station_info = scraper.get_station_info("NDLS")
if station_info:
    print(f"Station: {station_info.get('station_name', 'N/A')}")
    print(f"Trains passing: {len(station_info.get('trains_passing', []))}")
```

## 🚉 Popular Station Codes

| Code | Station Name |
|------|-------------|
| NDLS | New Delhi |
| MMCT | Mumbai Central |
| MAS | Chennai Central |
| KOAA | Kolkata |
| SBC | Bangalore City |
| HYB | Hyderabad |
| PUNE | Pune Junction |
| ADI | Ahmedabad Junction |
| JP | Jaipur Junction |
| LJN | Lucknow Junction |
| BBS | Bhubaneswar |
| VSKP | Visakhapatnam |
| TVC | Trivandrum Central |
| JAT | Jammu Tawi |
| GHY | Guwahati |

## 🔧 Configuration

### Proxy Settings

The scraper automatically loads proxies from these files:
- `ssl_proxies.txt`
- `google_proxies.txt`
- `anany_proxies.txt`
- `new_proxies.txt`

### Request Headers

The scraper uses realistic browser headers:
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}
```

### Delay Settings

Random delays between requests: 2-5 seconds
```python
time.sleep(random.uniform(2, 5))
```

## 📊 Data Output

### Train Data Structure

```json
{
    "train_number": "12951",
    "train_name": "Mumbai Rajdhani Express",
    "from_station": "NDLS",
    "to_station": "MMCT",
    "departure_time": "16:55",
    "arrival_time": "08:35",
    "classes_available": "1A, 2A, 3A",
    "scraped_at": "2024-12-20T10:30:00",
    "source": "Indian Railway Official"
}
```

### Schedule Data Structure

```json
{
    "train_number": "12951",
    "stations": [
        {
            "station": "New Delhi",
            "arrival": "16:55",
            "departure": "16:55",
            "distance": "0"
        },
        {
            "station": "Kota Jn",
            "arrival": "22:25",
            "departure": "22:30",
            "distance": "465"
        }
    ],
    "scraped_at": "2024-12-20T10:30:00"
}
```

### Station Data Structure

```json
{
    "station_code": "NDLS",
    "station_name": "New Delhi",
    "trains_passing": [
        {
            "train_number": "12951",
            "train_name": "Mumbai Rajdhani Express",
            "arrival": "16:55",
            "departure": "16:55"
        }
    ],
    "scraped_at": "2024-12-20T10:30:00"
}
```

## 🛡️ Safety Features

### Proxy Rotation
- **Round-robin rotation**: Each request uses a different proxy
- **Failure tracking**: Automatically removes unreliable proxies
- **Success rate monitoring**: Tracks proxy performance
- **Fallback to direct**: Uses direct connection if all proxies fail

### Rate Limiting
- **Random delays**: 2-5 seconds between requests
- **Request throttling**: Prevents overwhelming the servers
- **Respectful scraping**: Follows ethical scraping practices

### Error Handling
- **Multiple retries**: Up to 3 attempts per request
- **Graceful degradation**: Falls back to alternative methods
- **Comprehensive logging**: Detailed error reporting
- **Exception handling**: Prevents crashes from network issues

## 🔍 Troubleshooting

### Common Issues

#### No Proxies Available
```
Warning: No proxy files found. Will use direct connection.
```
**Solution**: Run `python3 proxy_scraper_advanced.py` to get fresh proxies.

#### All Proxies Failed
```
All attempts failed
```
**Solutions**:
1. Get fresh proxies: `python3 proxy_scraper_advanced.py`
2. Check internet connection
3. Try again later (servers might be busy)

#### No Data Found
```
No trains found for this route
```
**Possible causes**:
1. Invalid station codes
2. No trains on this route/date
3. Website structure changes
4. All proxies blocked

#### SSL Certificate Errors
The scraper uses `verify=False` to handle SSL issues with some Indian Railway sites.

### Debug Mode

Enable debug mode for detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## ⚖️ Legal Notice

### Important Disclaimers

1. **Educational Purpose**: This tool is created for educational and research purposes only.

2. **Respect Terms of Service**: Always respect the website's terms of service and robots.txt file.

3. **Rate Limiting**: The tool implements delays and proxy rotation to be respectful to servers.

4. **No Warranty**: This software is provided "as is" without any warranty.

5. **User Responsibility**: Users are responsible for complying with applicable laws and regulations.

### Best Practices

1. **Use Responsibly**: Don't overload the servers with too many requests
2. **Respect Delays**: Don't modify the delay settings to be more aggressive
3. **Check robots.txt**: Respect the website's crawling guidelines
4. **Personal Use**: Use for personal research and educational purposes only
5. **No Commercial Use**: Don't use for commercial purposes without permission

## 🤝 Contributing

### Reporting Issues

If you encounter issues:
1. Check the troubleshooting section
2. Ensure you have fresh proxies
3. Verify your internet connection
4. Report bugs with detailed error messages

### Improvements

Potential improvements:
- Support for more Indian Railway websites
- Better parsing algorithms
- Additional data fields
- Performance optimizations
- More proxy sources

## 📝 Changelog

### Version 1.0.0
- Initial release with proxy rotation
- Command-line interface
- Web application interface
- Train search functionality
- Schedule lookup
- Station information
- Comprehensive error handling
- Safety features implementation

## 🙏 Acknowledgments

- **Indian Railways**: For providing public access to train information
- **Proxy Providers**: For enabling safe scraping through IP rotation
- **Open Source Community**: For the tools and libraries used in this project

---

**Remember**: Use this tool responsibly and ethically. Always respect the website's terms of service and don't overload their servers. Happy and safe scraping! 🚂✨ 