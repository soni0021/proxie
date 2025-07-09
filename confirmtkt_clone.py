#!/usr/bin/env python3
"""
ConfirmTkt Clone - Railway Information Service
A comprehensive train information service that provides:
- Live train status tracking
- Train schedule information  
- PNR status checking
- Smart proxy rotation for reliable service
"""

import os
import sys
import json
import time
import random
import re
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, make_response
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ProxyRotator:
    def __init__(self):
        self.proxies = []
        self.current_index = 0
        self.last_shuffle = time.time()
        self.shuffle_interval = 300  # 5 minutes
        self.proxy_stats = {}  # Track proxy performance
        self.failed_proxies = set()  # Track temporarily failed proxies
        self.max_failures = 3  # Max failures before temporary blacklist
        self.failure_timeout = 300  # 5 minutes timeout for failed proxies
        self.fast_proxies = []  # List of proxies with good response times
        self.load_proxies()

    def load_proxies(self):
        """Load proxies with performance data"""
        try:
            # Load detailed proxy information
            with open('working_proxies_detailed.json', 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'working_proxies' in data:
                    # Sort proxies by response time
                    proxies = data['working_proxies']
                    proxies.sort(key=lambda x: x['timings']['total'])
                    
                    # Keep track of fast proxies (response time < 2 seconds)
                    for proxy_info in proxies:
                        if isinstance(proxy_info, dict) and 'proxy' in proxy_info:
                            proxy = proxy_info['proxy']
                            self.proxies.append(proxy)
                            response_time = proxy_info['timings']['total']
                            
                            if response_time < 2.0:  # Fast proxy threshold
                                self.fast_proxies.append(proxy)
                                
                            self.proxy_stats[proxy] = {
                                'success': 0,
                                'failure': 0,
                                'last_success': None,
                                'last_failure': None,
                                'avg_response': response_time,
                                'last_used': 0
                            }
        except Exception as e:
            print(f"Error loading working_proxies_detailed.json: {str(e)}")
            
        # Fallback to simple proxy list if detailed info not available
        if not self.proxies:
            try:
                with open('working_proxies.txt', 'r') as f:
                    self.proxies = [line.strip() for line in f if line.strip()]
                    for proxy in self.proxies:
                        self.proxy_stats[proxy] = {
                            'success': 0,
                            'failure': 0,
                            'last_success': None,
                            'last_failure': None,
                            'avg_response': float('inf'),
                            'last_used': 0
                        }
            except Exception as e:
                print(f"Error loading working_proxies.txt: {str(e)}")
            
        # Add backup proxies if no proxies loaded
        if not self.proxies:
            backup_proxies = [
                "188.166.230.109:31028",  # Fastest from last test
                "161.35.70.249:8080",
                "138.68.60.8:80",
                "35.179.146.181:3128",
                "51.81.245.3:17981"
            ]
            self.proxies = backup_proxies
            self.fast_proxies = backup_proxies[:2]  # Consider first two as fast
            for proxy in backup_proxies:
                self.proxy_stats[proxy] = {
                    'success': 0,
                    'failure': 0,
                    'last_success': None,
                    'last_failure': None,
                    'avg_response': float('inf'),
                    'last_used': 0
                }
        
        print(f"Loaded {len(self.proxies)} proxies ({len(self.fast_proxies)} fast) for rotation")
        random.shuffle(self.proxies)  # Initial shuffle

    def update_proxy_stats(self, proxy, success, response_time=None):
        """Update proxy statistics"""
        if proxy not in self.proxy_stats:
            return
            
        stats = self.proxy_stats[proxy]
        current_time = time.time()
        
        if success:
            stats['success'] += 1
            stats['last_success'] = current_time
            if response_time:
                # Update moving average of response time
                if stats['avg_response'] == float('inf'):
                    stats['avg_response'] = response_time
                else:
                    stats['avg_response'] = (stats['avg_response'] * 0.7) + (response_time * 0.3)
                
                # Update fast proxies list
                if response_time < 2.0 and proxy not in self.fast_proxies:
                    self.fast_proxies.append(proxy)
                elif response_time >= 2.0 and proxy in self.fast_proxies:
                    self.fast_proxies.remove(proxy)
            
            # Remove from failed proxies if present
            self.failed_proxies.discard(proxy)
        else:
            stats['failure'] += 1
            stats['last_failure'] = current_time
            
            # Add to failed proxies if max failures reached
            if stats['failure'] >= self.max_failures:
                self.failed_proxies.add(proxy)
                if proxy in self.fast_proxies:
                    self.fast_proxies.remove(proxy)
        
        stats['last_used'] = current_time

    def clean_failed_proxies(self):
        """Remove proxies from failed list after timeout"""
        current_time = time.time()
        for proxy in list(self.failed_proxies):
            stats = self.proxy_stats[proxy]
            if current_time - stats['last_failure'] > self.failure_timeout:
                self.failed_proxies.discard(proxy)
                stats['failure'] = 0  # Reset failure count

    def get_proxy(self):
        """Get next best proxy using smart rotation"""
        if not self.proxies:
            return None
    
        # Clean up failed proxies
        self.clean_failed_proxies()
        
        current_time = time.time()
        
        # First try fast proxies that haven't been used recently
        for proxy in self.fast_proxies:
            if proxy not in self.failed_proxies:
                stats = self.proxy_stats[proxy]
                if current_time - stats['last_used'] > 1:  # 1 second cooldown
                    return proxy
        
        # If no fast proxies available, try regular proxies
        attempts = 0
        max_attempts = len(self.proxies)
        
        while attempts < max_attempts:
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            
            if proxy not in self.failed_proxies:
                stats = self.proxy_stats[proxy]
                if current_time - stats['last_used'] > 1:  # 1 second cooldown
                    return proxy
            
            attempts += 1
            
        # If all proxies failed, try the least recently failed one
        if self.failed_proxies:
            least_recent_failed = min(
                self.failed_proxies,
                key=lambda p: self.proxy_stats[p]['last_failure'] or 0
            )
            return least_recent_failed
            
        return self.proxies[0]  # Last resort

class ConfirmTktAPI:
    def __init__(self):
        self.base_url = "https://www.confirmtkt.com"
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.proxy_rotator = ProxyRotator()
        self.max_retries = 3
        self.retry_delay = 2
        print("Starting ConfirmTkt Clone server...")
        print("Proxy rotation enabled with smart retry logic")
        
    def make_request_with_proxy(self, url, method='get', **kwargs):
        """Make HTTP request with smart proxy rotation and retry logic"""
        retries = 0
        max_retries = 2  # Reduced from 3 to 2 for faster response
        initial_timeout = 10  # Initial timeout of 10 seconds
        
        # Set default timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = initial_timeout
            
        # Set default headers if not provided
        if 'headers' not in kwargs:
            kwargs['headers'] = self.base_headers.copy()
        
        # Add cache control headers
        kwargs['headers'].update({
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        while retries < max_retries:
            try:
                # Always use proxy - never expose real IP
                proxy = self.proxy_rotator.get_proxy()
                if not proxy:
                    print("No proxies available!")
                    return None
        
                # Format proxy URL
                proxy_url = f"http://{proxy}" if not proxy.startswith('http') else proxy
                kwargs['proxies'] = {'http': proxy_url, 'https': proxy_url}
                
                # Make request and measure time
                start_time = time.time()
                
                # Use session for connection pooling
                with requests.Session() as session:
                    # Set session-level parameters
                    session.verify = False
                    session.headers.update(kwargs['headers'])
                    session.proxies = kwargs['proxies']
                    
                    # Make the request
                    response = session.request(method, url, **{k:v for k,v in kwargs.items() if k not in ['headers', 'proxies', 'verify']})
                    
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    # Update proxy stats with success
                    self.proxy_rotator.update_proxy_stats(proxy, True, response_time)
                    return response
                elif response.status_code == 404:
                    # Don't retry on 404, but mark proxy as working
                    self.proxy_rotator.update_proxy_stats(proxy, True, response_time)
                    return response
                else:
                    # Mark proxy as failed for non-200 responses
                    self.proxy_rotator.update_proxy_stats(proxy, False)
                    print(f"Request failed with status {response.status_code}, trying different proxy...")
                    
            except requests.exceptions.Timeout:
                # For timeout errors, mark proxy as failed but don't increase timeout
                if proxy:
                    self.proxy_rotator.update_proxy_stats(proxy, False)
                print(f"Request timeout with proxy {proxy}")
                
            except requests.exceptions.RequestException as e:
                # Mark proxy as failed on connection errors
                if proxy:
                    self.proxy_rotator.update_proxy_stats(proxy, False)
                print(f"Request error with proxy {proxy}: {str(e)}")
                
            except Exception as e:
                if proxy:
                    self.proxy_rotator.update_proxy_stats(proxy, False)
                print(f"Unexpected error with proxy {proxy}: {str(e)}")
            
            retries += 1
            if retries < max_retries:
                time.sleep(1)  # Fixed 1 second delay between retries
        
        return None
    
    def clean_text(self, text):
        """Clean text by removing extra whitespace and newlines"""
        if not text:
            return ''
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text

    def clean_station_name(self, text):
        """Clean station name by removing codes and standardizing format"""
        if not text:
            return ''
            
        # Remove station code at end (e.g. " - HWH" or " - NDLS")
        text = re.sub(r'\s*-\s*[A-Z]{2,5}$', '', text)
        
        # Remove common suffixes
        text = re.sub(r'\s*(?:Jn|Junction|Junc|Stn|Station|Halt|H|Terminal|Term)\s*$', '', text, flags=re.IGNORECASE)
        
        # Clean up remaining text
        return self.clean_text(text)

    def parse_station_info(self, text):
        """Parse station info from text containing date/time/status"""
        if not text:
            return None
    
        # Try to extract station name
        station_pattern = r'^([A-Za-z\s\(\)-]+?)(?:\s*-\s*[A-Z]{2,5})?(?:Day\s+\d|[\d:]+|Right Time|Late by|Delay by|Running|Departed|Arrived)'
        station_match = re.search(station_pattern, text)
        if station_match:
            return self.clean_station_name(station_match.group(1))
            
        # If no match, clean the original text
        return self.clean_station_name(text)

    def parse_station_row(self, text):
        """Parse a live status row into station data"""
        if not text:
            return None
            
        # Initialize station data
        station_data = {
            'station': '',
            'date': '',
            'arrives': '',
            'departs': '',
            'delay': '',
            'status': 'upcoming'
        }
        
        # Extract station name
        station_name = self.parse_station_info(text)
        if not station_name:
            return None
            
        # Skip if this looks like a delay message
        if any(d in station_name.lower() for d in ['delay', 'late']):
            return None
            
        station_data['station'] = station_name
        
        # Extract date (Day X-Mon)
        date_match = re.search(r'Day\s+(\d+)[-\s]*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[-\s]*\d+)?', text)
        if date_match:
            day = date_match.group(1)
            month = date_match.group(2) if date_match.group(2) else ''
            station_data['date'] = f"Day {day} {month}".strip()
        
        # Extract times (HH:MM)
        time_matches = re.findall(r'\d{2}:\d{2}', text)
        if len(time_matches) >= 2:
            station_data['arrives'] = time_matches[0]
            station_data['departs'] = time_matches[1]
        elif len(time_matches) == 1:
            if 'arrives' in text.lower():
                station_data['arrives'] = time_matches[0]
            else:
                station_data['departs'] = time_matches[0]
        
        # Extract delay info
        delay_match = re.search(r'(?:Late by|Delay(?:ed)? by)\s+(\d+)\s*(?:min(?:ute)?s?|hrs?|hours?)', text, re.IGNORECASE)
        if delay_match:
            delay_mins = delay_match.group(1)
            station_data['delay'] = f"Delayed by {delay_mins} minutes"
        elif 'Right Time' in text:
            station_data['delay'] = 'On Time'
        
        return station_data

    def parse_route(self, text):
        """Extract clean route information from text"""
        if not text:
            return ''
            
        # Remove unwanted text
        text = re.sub(r'\s*Change\s*', '', text)
        text = re.sub(r'\s*Running Days\s*', '', text)
        text = re.sub(r'\n+', ' ', text)
        
        # Try to extract route with station names
        route_patterns = [
            r'([A-Za-z\s]+)\s+to\s+([A-Za-z\s]+)',
            r'From\s+([A-Za-z\s]+)\s+To\s+([A-Za-z\s]+)',
            r'([A-Z]{3,4})\s+to\s+([A-Z]{3,4})'
        ]
        
        for pattern in route_patterns:
            match = re.search(pattern, text)
            if match:
                from_station = self.clean_station_name(match.group(1))
                to_station = self.clean_station_name(match.group(2))
                if from_station and to_station:
                    return f"{from_station} to {to_station}"
        
        return self.clean_text(text)

    def parse_schedule_row(self, cols):
        """Parse a schedule table row into station data"""
        if not cols or len(cols) < 3:
            return None
            
        try:
            # Initialize with empty values
            station_data = {
                'sr_no': '',
                'station': '',
                'code': '',
                'arrives': '',
                'departs': '',
                'halt': '',
                'distance': '',
                'avg_delay': '',
                'day': '1'
            }
            
            # Get station name from first column
            station_text = cols[0].text.strip()
            if not station_text or station_text.lower() in ['s.no', 'sr.no', 'station', 'stations']:
                return None
                
            # Fast path for common table format
            if station_text.isdigit():
                station_data['sr_no'] = station_text
                
                # Station name and code
                station_name = cols[1].text.strip()
                station_code_match = re.search(r'(.*?)\s*-\s*([A-Z]{2,5})$', station_name)
                if station_code_match:
                    station_data.update({
                        'station': self.clean_station_name(station_code_match.group(1)),
                        'code': station_code_match.group(2)
                    })
                else:
                    station_data['station'] = self.clean_station_name(station_name)
                
                # Direct column mapping for speed
                if len(cols) > 2: station_data['arrives'] = self.parse_time(cols[2].text.strip())
                if len(cols) > 3: station_data['departs'] = self.parse_time(cols[3].text.strip())
                if len(cols) > 4: station_data['halt'] = cols[4].text.strip()
                if len(cols) > 5: station_data['distance'] = re.sub(r'[^\d.]', '', cols[5].text.strip())
                if len(cols) > 6: station_data['avg_delay'] = self.parse_delay(cols[6].text.strip())
                if len(cols) > 7: station_data['day'] = cols[7].text.strip()
            else:
                # Alternative format handling
                station_code_match = re.search(r'(.*?)\s*-\s*([A-Z]{2,5})$', station_text)
                if station_code_match:
                    station_data.update({
                        'station': self.clean_station_name(station_code_match.group(1)),
                        'code': station_code_match.group(2)
                    })
                else:
                    station_data['station'] = self.clean_station_name(station_text)
                
                # Direct column mapping
                if len(cols) > 1: station_data['arrives'] = self.parse_time(cols[1].text.strip())
                if len(cols) > 2: station_data['departs'] = self.parse_time(cols[2].text.strip())
                if len(cols) > 3: station_data['distance'] = re.sub(r'[^\d.]', '', cols[3].text.strip())
            
            # Quick validation
            if not station_data['station']:
                return None
                
            # Clean arrival/departure
            if station_data['arrives'].lower() in ['source', 'start', '']:
                station_data['arrives'] = 'Start'
            if station_data['departs'].lower() in ['destination', 'end', '']:
                station_data['departs'] = 'End'
                
            # Clean halt time
            if station_data['halt']:
                halt_match = re.search(r'(\d+)\s*(?:min|m)', station_data['halt'], re.IGNORECASE)
                if halt_match:
                    station_data['halt'] = f"{halt_match.group(1)}m"
            
            return station_data
            
        except Exception as e:
            print(f"Error parsing schedule row: {str(e)}")
            return None
    
    def parse_time(self, text):
        """Extract time from text in HH:MM format"""
        time_match = re.search(r'(\d{1,2}:\d{2})', text)
        return time_match.group(1) if time_match else ''

    def parse_delay(self, text):
        """Extract delay information from text"""
        if not text:
            return ''
            
        delay_pattern = r'(?:Late by|Delay(?:ed)? by|Running late by)\s+(\d+)\s*(?:min|minutes|hrs|hours)'
        delay_match = re.search(delay_pattern, text, re.IGNORECASE)
        if delay_match:
            return f"{delay_match.group(1)} Min"
        elif 'Right Time' in text or 'On Time' in text:
            return ''
        return ''

    def get_train_name(self, soup, train_number):
        """Extract train name from multiple sources"""
        # Try JSON-LD script first
        json_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Check for train name in JSON data
                    if 'name' in data and train_number in str(data['name']):
                        name = self.clean_text(data['name'])
                        if name != train_number:
                            return name.replace(train_number, '').strip()
                    # Check for train info object
                    if 'TrainName' in data:
                        name = self.clean_text(data['TrainName'])
                        if name and name != train_number:
                            return name
            except:
                continue
                
        # Try finding in script data
        scripts = soup.find_all('script', type='text/javascript')
        for script in scripts:
            if script.string and 'trainName' in script.string:
                try:
                    # Look for trainName assignment
                    match = re.search(r'trainName\s*=\s*["\']([^"\']+)["\']', script.string)
                    if match:
                        name = self.clean_text(match.group(1))
                        if name and name != train_number:
                            return name
                    # Look for data object with TrainName
                    match = re.search(r'data\s*=\s*({[^;]+})', script.string)
                    if match:
                        data = json.loads(match.group(1))
                        if 'TrainName' in data:
                            name = self.clean_text(data['TrainName'])
                            if name and name != train_number:
                                return name
                except:
                    continue
        
        # Try title and h1/h2 headers
        for element in soup.find_all(['title', 'h1', 'h2']):
            text = element.text.strip()
            if train_number in text and text != train_number:
                # Remove common suffixes
                text = re.sub(r'\s*(?:Train Route|Train Schedule|Running Status|Live Status|Train running status|Spot your train).*$', '', text, flags=re.IGNORECASE)
                # Extract name part
                name_match = re.search(f"{train_number}\\s*[-/]\\s*([^-/]+)", text)
                if name_match:
                    name = self.clean_text(name_match.group(1))
                    if name and name != train_number:
                        return name
                # Try extracting from parentheses
                name_match = re.search(r'\((.*?)\)', text)
                if name_match:
                    name = self.clean_text(name_match.group(1))
                    if name and name != train_number:
                        return name
                
        # Try finding in page content with expanded patterns
        train_name_patterns = [
            f"{train_number}\\s*[-/]\\s*([A-Za-z\\s]+?)(?:\\s+(?:EXP|EXPRESS|MAIL|SF|SPL|SPECIAL|FEST|FESTIVAL|LINK|PASSENGER|PASS|LOCAL|SHUTTLE|MEMU|DEMU|EMU|INTERCITY|SUPERFAST|RAJDHANI|SHATABDI|DURONTO|GARIB|RATH|HUMSAFAR|TEJAS|VANDE|BHARAT))",
            f"{train_number}\\s+([A-Za-z\\s]+?)(?:\\s+(?:EXP|EXPRESS|MAIL|SF|SPL|SPECIAL|FEST|FESTIVAL|LINK|PASSENGER|PASS|LOCAL|SHUTTLE|MEMU|DEMU|EMU|INTERCITY|SUPERFAST|RAJDHANI|SHATABDI|DURONTO|GARIB|RATH|HUMSAFAR|TEJAS|VANDE|BHARAT))",
            f"([A-Za-z\\s]+?)(?:\\s+(?:EXP|EXPRESS|MAIL|SF|SPL|SPECIAL|FEST|FESTIVAL|LINK|PASSENGER|PASS|LOCAL|SHUTTLE|MEMU|DEMU|EMU|INTERCITY|SUPERFAST|RAJDHANI|SHATABDI|DURONTO|GARIB|RATH|HUMSAFAR|TEJAS|VANDE|BHARAT))\\s*[-/]?\\s*{train_number}",
            f"{train_number}\\s*[-/]\\s*([A-Za-z\\s]+)",
            f"([A-Za-z\\s]+)\\s*[-/]\\s*{train_number}"
        ]
        
        page_text = soup.get_text()
        for pattern in train_name_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                name = match.group(1).strip() if match.lastindex else match.group().strip()
                if name and name != train_number:
                    name = self.clean_text(name)
                    # Remove train number if present
                    name = re.sub(f"\\s*{train_number}\\s*", '', name)
                    if name:
                        return name
        
        # Try finding train name in table headers or cells
        tables = soup.find_all('table')
        for table in tables:
            # Check table headers and cells
            for cell in table.find_all(['th', 'td']):
                cell_text = cell.text.strip()
                if train_number in cell_text:
                    # Try extracting name from cell
                    name_match = re.search(f"{train_number}\\s*[-/]\\s*([^-/]+)", cell_text)
                    if name_match:
                        name = self.clean_text(name_match.group(1))
                        if name and name != train_number:
                            return name
                    # Try extracting from parentheses
                    name_match = re.search(r'\((.*?)\)', cell_text)
                    if name_match:
                        name = self.clean_text(name_match.group(1))
                        if name and name != train_number:
                            return name
        
        # Try finding in specific elements with train-related classes
        train_elements = soup.find_all(class_=lambda x: x and any(c in str(x).lower() for c in ['train', 'schedule', 'status']))
        for element in train_elements:
            text = element.text.strip()
            if train_number in text:
                # Try various patterns
                for pattern in [
                    f"{train_number}\\s*[-/]\\s*([^-/]+)",
                    r'\((.*?)\)',
                    f"([A-Za-z\\s]+)\\s*[-/]\\s*{train_number}"
                ]:
                    match = re.search(pattern, text)
                    if match:
                        name = self.clean_text(match.group(1))
                        if name and name != train_number:
                            return name
        
        return "Train"  # Default fallback if no name found

    def get_route_info(self, soup):
        """Extract route information from multiple sources"""
        # Look for route in specific elements first
        route_elements = soup.find_all(['div', 'p', 'span'], class_=lambda x: x and any(
            c in str(x).lower() for c in ['route', 'path', 'direction', 'journey']
        ))
        
        for element in route_elements:
            route = self.parse_route(element.get_text())
            if route and ' to ' in route:
                return route
        
        # Try finding in page content
        route_patterns = [
            r'(?:From|Source)\s*:\s*([A-Za-z\s]+)\s+(?:To|Destination)\s*:\s*([A-Za-z\s]+)',
            r'([A-Za-z\s]+)\s+to\s+([A-Za-z\s]+)',
            r'([A-Za-z\s]+)\s*-\s*([A-Za-z\s]+)\s+Route',
            r'Route\s*:\s*([A-Za-z\s]+)\s*-\s*([A-Za-z\s]+)'
        ]
        
        page_text = soup.get_text()
        for pattern in route_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                from_station = self.clean_station_name(match.group(1))
                to_station = self.clean_station_name(match.group(2))
                if from_station and to_station:
                    return f"{from_station} to {to_station}"
        
        return ''

    def get_running_days(self, soup):
        """Extract running days from multiple sources"""
        # Common day patterns
        day_patterns = [
            r'(?:Running|Runs)\s+(?:Days|on)\s*[:\s]*((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)(?:\s*[,&]\s*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun))*)',
            r'(?:Running|Runs)\s+(?:on|every)\s+((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)(?:\s*[,&]\s*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun))*)',
            r'((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)(?:\s*[,&]\s*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun))*)\s+only',
            r'Daily',
            r'All Days'
        ]
        
        # Look in specific elements first
        running_elements = soup.find_all(['div', 'p', 'span'], class_=lambda x: x and any(
            c in str(x).lower() for c in ['running', 'schedule', 'frequency', 'days']
        ))
        
        for element in running_elements:
            text = element.get_text()
            if 'Daily' in text or 'All Days' in text:
                return 'Daily'
                
            for pattern in day_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    days = match.group(1) if match.lastindex else match.group()
                    days = re.sub(r'\s*[,&]\s*', ', ', days)  # Standardize separators
                    return self.clean_text(days)
        
        # Try finding in page content
        page_text = soup.get_text()
        if 'Daily' in page_text or 'All Days' in page_text:
            return 'Daily'
            
        for pattern in day_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                days = match.group(1) if match.lastindex else match.group()
                days = re.sub(r'\s*[,&]\s*', ', ', days)  # Standardize separators
                return self.clean_text(days)
        
        return 'Daily'  # Default to Daily if no specific days found

    def get_train_schedule(self, train_number):
        """Get train schedule using ConfirmTkt API"""
        try:
            # Use cached response if available
            cache_key = f"schedule_{train_number}"
            cached_response = getattr(self, cache_key, None)
            if cached_response and time.time() - cached_response['timestamp'] < 3600:  # 1 hour cache
                return cached_response['data']

            main_url = f"{self.base_url}/train-schedule/{train_number}"
            
            # Use session for connection pooling and set aggressive timeouts
            with requests.Session() as session:
                session.verify = False
                session.headers.update(self.base_headers)
                session.headers.update({
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                })
                
                response = self.make_request_with_proxy(
                    main_url,
                    timeout=10,  # 10 second timeout
                    verify=False
                )
            
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Initialize response structure
                result = {
                    'train_number': train_number,
                    'train_name': '',
                    'route': '',
                    'running_days': '',
                    'stations': []
                }
                
                # Parallel extraction of basic info
                # Extract train name from title or meta description first (fastest)
                title = soup.find('title')
                if title:
                    title_text = title.text
                    train_name_match = re.search(f"{train_number}\\s*[-/]\\s*([^-/]+)", title_text)
                    if train_name_match:
                        result['train_name'] = self.clean_text(train_name_match.group(1))
                
                if not result['train_name']:
                    meta_desc = soup.find('meta', {'name': 'description'})
                    if meta_desc:
                        desc_text = meta_desc.get('content', '')
                        train_name_match = re.search(f"{train_number}\\s*[-/]\\s*([^-/]+)", desc_text)
                        if train_name_match:
                            result['train_name'] = self.clean_text(train_name_match.group(1))
                
                # Only do expensive name search if still not found
                if not result['train_name']:
                    result['train_name'] = self.get_train_name(soup, train_number)
                
                # Find schedule table directly - most important data
                tables = soup.find_all('table')
                schedule_found = False
                seen_stations = set()
                
                for table in tables:
                    rows = table.find_all('tr')
                    if len(rows) > 1:
                        # Quick check for schedule table
                        header_cells = [cell.text.strip().lower() for cell in rows[0].find_all(['th', 'td'])]
                        if any(indicator in ' '.join(header_cells) for indicator in ['station', 'arrives', 'departs']):
                            schedule_found = True
                            
                            # Process schedule rows in parallel
                            for row in rows[1:]:
                                cols = row.find_all(['td', 'th'])
                                station_data = self.parse_schedule_row(cols)
                                
                                if station_data and station_data['station'] not in seen_stations:
                                    seen_stations.add(station_data['station'])
                                    result['stations'].append(station_data)
                
                # Extract route and running days in parallel if schedule found
                if schedule_found:
                    # Extract route from first/last station if available
                    if len(result['stations']) >= 2:
                        first_station = result['stations'][0]['station']
                        last_station = result['stations'][-1]['station']
                        result['route'] = f"{first_station} to {last_station}"
                    
                    # Quick running days check
                    page_text = soup.get_text()
                    if 'Daily' in page_text or 'All Days' in page_text:
                        result['running_days'] = 'Daily'
                    else:
                        result['running_days'] = self.get_running_days(soup)
                else:
                    # Fallback to slower extraction methods
                    result['route'] = self.get_route_info(soup)
                    result['running_days'] = self.get_running_days(soup)
                
                # Cache the response
                setattr(self, cache_key, {
                    'timestamp': time.time(),
                    'data': {
                        'status': 'success',
                        'message': 'Schedule fetched successfully',
                        'data': result
                    }
                })
                
                return {
                    'status': 'success',
                    'message': 'Schedule fetched successfully',
                    'data': result
                }
                
            return {
                'status': 'error',
                'message': 'Failed to get train schedule'
            }
                
        except Exception as e:
            print(f"Error getting train schedule: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to get train schedule: {str(e)}'
            }

    def get_pnr_status(self, pnr_number):
        """Get PNR status using ConfirmTkt API"""
        try:
            main_url = f"{self.base_url}/pnr-status/{pnr_number}"
            response = self.make_request_with_proxy(
                main_url,
                headers=self.base_headers,
                verify=False
            )
            
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Initialize response structure to match the desired format
                result = {
                    'pnr': pnr_number,
                    'train_number': '',
                    'train_name': '',
                    'train_journey': {
                        'from': '',
                        'to': '',
                        'date': '',
                        'platform': '',
                        'class': '',
                        'quota': ''
                    },
                    'passengers': [],
                    'chart_status': 'Chart not prepared',
                    'rating': None
                }
                
                # Extract train number and name from title or headers
                title = soup.find('title')
                if title:
                    title_text = title.text
                    # Look for train number pattern
                    train_match = re.search(r'(\d{5})', title_text)
                    if train_match:
                        result['train_number'] = train_match.group(1)
                
                # Look for train information in the page content
                page_text = soup.get_text()
                
                # Extract train name (e.g., "15013 - RANIKHET EXP")
                train_name_match = re.search(r'(\d{5})\s*-\s*([A-Z\s]+(?:EXP|EXPRESS|MAIL|SF))', page_text)
                if train_name_match:
                    result['train_number'] = train_name_match.group(1)
                    result['train_name'] = train_name_match.group(2).strip()
                
                # Extract journey information
                # Look for route pattern (e.g., "Rajgarh - RHG, 17:05 → Kathgodam - KGM, 05:05")
                route_match = re.search(r'([A-Za-z\s]+)\s*-\s*([A-Z]{3,4}),\s*(\d{2}:\d{2})\s*→\s*([A-Za-z\s]+)\s*-\s*([A-Z]{3,4}),\s*(\d{2}:\d{2})', page_text)
                if route_match:
                    result['train_journey']['from'] = f"{route_match.group(1).strip()} - {route_match.group(2)}, {route_match.group(3)}"
                    result['train_journey']['to'] = f"{route_match.group(4).strip()} - {route_match.group(5)}, {route_match.group(6)}"
                
                # Extract date and class information
                # Look for date pattern (e.g., "Fri, 11 Jul | SL | GN | Expected platform: 4")
                date_class_match = re.search(r'([A-Za-z]{3}),\s*(\d{1,2}\s+[A-Za-z]{3})\s*\|\s*([A-Z]{1,3})\s*\|\s*([A-Z]{1,3})\s*\|\s*Expected platform:\s*(\d+)', page_text)
                if date_class_match:
                    result['train_journey']['date'] = f"{date_class_match.group(1)}, {date_class_match.group(2)}"
                    result['train_journey']['class'] = date_class_match.group(3)
                    result['train_journey']['quota'] = date_class_match.group(4)
                    result['train_journey']['platform'] = date_class_match.group(5)
                
                # Extract chart status
                chart_match = re.search(r'Chart (not prepared|prepared)', page_text, re.IGNORECASE)
                if chart_match:
                    result['chart_status'] = f"Chart {chart_match.group(1)}"
                
                # Look for passenger information table
                # Find table with passenger data
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    if len(rows) > 1:
                        # Check if this looks like a passenger table
                        header_row = rows[0]
                        headers = [th.get_text().strip().lower() for th in header_row.find_all(['th', 'td'])]
                        
                        if any(h in ' '.join(headers) for h in ['passenger', 'current', 'booking', 'status', 'coach']):
                            print(f"Found passenger table with headers: {headers}")
                            
                            for i, row in enumerate(rows[1:], 1):
                                cols = row.find_all(['td', 'th'])
                                if len(cols) >= 3:
                                    passenger = {
                                        'sr_no': str(i),
                                        'current_status': {
                                            'status': '',
                                            'available': False,
                                            'coach': '',
                                            'berth': ''
                                        },
                                        'booking_status': '',
                                        'coach': ''
                                    }
                                    
                                    # Extract current status (first column after S.No)
                                    if len(cols) >= 2:
                                        current_status_text = cols[1].get_text().strip()
                                        passenger['current_status']['status'] = current_status_text
                                        
                                        # Check if it's available (green text or "Available" keyword)
                                        if 'available' in current_status_text.lower() or cols[1].find('span', style=lambda x: x and 'green' in str(x).lower()):
                                            passenger['current_status']['available'] = True
                                        
                                        # Parse RAC/berth information
                                        rac_match = re.search(r'(RAC|GNWL|CNF)\s*(\d+)', current_status_text)
                                        if rac_match:
                                            passenger['current_status']['coach'] = rac_match.group(1)
                                            passenger['current_status']['berth'] = rac_match.group(2)
                                    
                                    # Extract booking status
                                    if len(cols) >= 3:
                                        booking_status_text = cols[2].get_text().strip()
                                        passenger['booking_status'] = booking_status_text
                                    
                                    # Extract coach information (if separate column)
                                    if len(cols) >= 4:
                                        coach_text = cols[3].get_text().strip()
                                        passenger['coach'] = coach_text if coach_text != '-' else ''
                                    
                                    result['passengers'].append(passenger)
                
                # If no table found, try to extract passenger info from divs/spans
                if not result['passengers']:
                    # Look for passenger status in various elements
                    passenger_elements = soup.find_all(['div', 'span'], class_=lambda x: x and any(
                        keyword in str(x).lower() for keyword in ['passenger', 'status', 'rac', 'gnwl', 'cnf']
                    ))
                    
                    passenger_count = 1
                    for element in passenger_elements:
                        text = element.get_text().strip()
                        if any(status in text for status in ['RAC', 'GNWL', 'CNF', 'Available']):
                            passenger = {
                                'sr_no': str(passenger_count),
                                'current_status': {
                                    'status': text,
                                    'available': 'available' in text.lower(),
                                    'coach': '',
                                    'berth': ''
                                },
                                'booking_status': '',
                                'coach': ''
                            }
                            
                            # Parse status
                            status_match = re.search(r'(RAC|GNWL|CNF)\s*(\d+)', text)
                            if status_match:
                                passenger['current_status']['coach'] = status_match.group(1)
                                passenger['current_status']['berth'] = status_match.group(2)
                            
                            result['passengers'].append(passenger)
                            passenger_count += 1
                
                # Extract rating if available
                rating_elements = soup.find_all(['span', 'div'], class_=lambda x: x and 'rating' in str(x).lower())
                for element in rating_elements:
                    rating_text = element.get_text()
                    rating_match = re.search(r'(\d+\.\d+)', rating_text)
                    if rating_match:
                        result['rating'] = float(rating_match.group(1))
                        break
                    
                print(f"PNR result: train={result['train_number']}, passengers={len(result['passengers'])}")
                return {
                    'status': 'success',
                    'message': 'PNR status fetched successfully',
                    'data': result
                }
            
            return {
                'status': 'error',
                'message': 'Failed to get PNR status'
            }
                
        except Exception as e:
            print(f"Error getting PNR status: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f'Failed to get PNR status: {str(e)}'
            }

    def parse_station_status(self, status_text):
        """Parse detailed station status information"""
        if not status_text:
            return []
            
        stations = []
        # Split by "Right Time" and clean up
        parts = status_text.split("Right Time")
        
        for part in parts:
            if not part.strip():
                continue
                
            # Extract station info using regex
            match = re.search(r'([A-Za-z\s]+?)(?:Day\s+(\d+)-Jul(\d+):(\d+):(\d+))?', part)
            if match:
                station_name = self.clean_station_name(match.group(1))
                if match.group(2):  # If time info exists
                    day = match.group(2)
                    month = "Jul"
                    hour = match.group(4)
                    minute = match.group(5)
                    
                    stations.append({
                        'station': station_name,
                        'date': f"Day {day}-{month}",
                        'time': f"{hour}:{minute}",
                        'status': 'Right Time'
                    })
                else:
                    stations.append({
                        'station': station_name,
                        'date': '',
                        'time': '',
                        'status': 'Right Time'
                    })
                    
        return stations

    def format_station_schedule(self, stations):
        """Format station schedule into a clean structure"""
        schedule = []
        current_found = False
        
        for i, station in enumerate(stations):
            schedule_entry = {
                'station': station['station'],
                'date': station['date'],
                'arrives': station['time'] if i > 0 else 'Start',
                'departs': station['time'],
                'status': 'Right Time'
            }
            
            # Set status based on position
            if not current_found and station['time']:
                schedule_entry['status'] = 'completed'
            elif not current_found and not station['time']:
                schedule_entry['status'] = 'current'
                current_found = True
            else:
                schedule_entry['status'] = 'upcoming'
            
            schedule.append(schedule_entry)
            
        return schedule

    def get_live_status(self, train_number):
        """Get live status using ConfirmTkt API"""
        try:
            # First try the running-status endpoint
            main_url = f"https://www.confirmtkt.com/train-running-status/{train_number}"
            response = self.make_request_with_proxy(
                main_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                },
                verify=False,
                timeout=30
            )
            
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Initialize response structure
                result = {
                    'train_number': train_number,
                    'train_name': '',
                    'current_status': '',
                    'current_station': '',
                    'next_station': '',
                    'last_updated': '',
                    'schedule': [],
                    'has_data': True
                }

                # Extract train name from title or meta description
                title = soup.find('title')
                if title:
                    title_text = title.text
                    # Try extracting from meta description first
                    meta_desc = soup.find('meta', {'name': 'description'})
                    if meta_desc:
                        desc_text = meta_desc.get('content', '')
                        # Pattern: "Live Train Status of DEE JU SF EXP and"
                        desc_match = re.search(r'Live Train Status of\s+([^\\s]+(?:\s+[^\\s]+)*?)\s+and', desc_text)
                        if desc_match:
                            result['train_name'] = desc_match.group(1).strip()
                        else:
                            result['train_name'] = f"Train {train_number}"
                    else:
                        result['train_name'] = f"Train {train_number}"

                # Look for the current status in train-update section
                train_update = soup.find('div', class_='train-update')
                if train_update:
                    status_div = train_update.find('div', class_='train-update__status')
                    if status_div:
                        status_text = status_div.get_text().strip()
                        result['current_status'] = status_text
                        
                        # Extract current station from status
                        if 'Yet to start from' in status_text:
                            result['current_station'] = 'Yet to start'
                        else:
                            # Try to extract current station name
                            station_match = re.search(r'at\\s+([^\\n]+)', status_text, re.IGNORECASE)
                            if station_match:
                                result['current_station'] = station_match.group(1).strip()
                    
                    # Get last updated time
                    time_div = train_update.find('div', class_='train-update__time')
                    if time_div:
                        time_text = time_div.get_text()
                        time_match = re.search(r'Last Updated:\s*([^,]+)', time_text)
                        if time_match:
                            result['last_updated'] = time_match.group(1).strip()

                # Look for the running status section with station information
                running_status = soup.find('div', class_='running-status')
                if running_status:
                    print("Found running-status section")
                    
                    # Find all station rows
                    station_rows = running_status.find_all('div', class_='well')
                    print(f"Found {len(station_rows)} station rows")
                    
                    current_found = False
                    for i, row in enumerate(station_rows):
                        station_row_div = row.find('div', class_='rs__station-row')
                        if station_row_div:
                            # Extract station information
                            station_grid = station_row_div.find('div', class_='rs__station-grid')
                            if station_grid:
                                # Get station name
                                station_name_span = station_grid.find('span', class_='rs__station-name')
                                if station_name_span:
                                    station_name = station_name_span.get_text().strip()
                                    
                                    # Check if this is the current station (has blinking circle)
                                    circle = station_grid.find('div', class_='circle')
                                    is_current = circle and 'blink' in circle.get('class', [])
                                    
                                    # Get all columns for this row
                                    cols = station_row_div.find_all('div', class_=lambda x: x and x.startswith('col-xs-'))
                                    
                                    station_data = {
                                        'station': self.clean_station_name(station_name),
                                        'date': '',
                                        'arrives': '',
                                        'departs': '',
                                        'status': 'Right Time'
                                    }
                                    
                                    # Extract date (Day X DD-Mon format)
                                    if len(cols) >= 2:
                                        date_col = cols[1]
                                        spans = date_col.find_all('span')
                                        if len(spans) >= 2:
                                            day = spans[0].get_text().strip()
                                            date = spans[1].get_text().strip()
                                            station_data['date'] = f"{day} {date}"
                                    
                                    # Extract arrival time
                                    if len(cols) >= 3:
                                        arrives_col = cols[2]
                                        arrives_span = arrives_col.find('span')
                                        if arrives_span:
                                            arrives_time = arrives_span.get_text().strip()
                                            if arrives_time:
                                                station_data['arrives'] = arrives_time
                                            elif i == 0:  # First station
                                                station_data['arrives'] = 'Start'
                                    
                                    # Extract departure time
                                    if len(cols) >= 4:
                                        departs_col = cols[3]
                                        departs_span = departs_col.find('span')
                                        if departs_span:
                                            departs_time = departs_span.get_text().strip()
                                            if departs_time:
                                                station_data['departs'] = departs_time
                                            elif i == len(station_rows) - 1:  # Last station
                                                station_data['departs'] = 'End'
                                    
                                    # Extract delay/status
                                    if len(cols) >= 5:
                                        status_col = cols[4]
                                        delay_div = status_col.find('div', class_='rs__station-delay')
                                        if delay_div:
                                            delay_text = delay_div.get_text().strip()
                                            station_data['status'] = delay_text
                                    
                                    # Set current station status
                                    if is_current:
                                        station_data['status'] = 'current'
                                        result['current_station'] = station_data['station']
                                        current_found = True
                                        
                                        # Set next station
                                        if i + 1 < len(station_rows):
                                            next_row = station_rows[i + 1]
                                            next_station_grid = next_row.find('div', class_='rs__station-grid')
                                            if next_station_grid:
                                                next_station_span = next_station_grid.find('span', class_='rs__station-name')
                                                if next_station_span:
                                                    result['next_station'] = self.clean_station_name(next_station_span.get_text().strip())
                                    elif not current_found:
                                        station_data['status'] = 'completed'
                                    else:
                                        station_data['status'] = 'upcoming'
                                    
                                    result['schedule'].append(station_data)
                                    print(f"Added station: {station_data['station']} - {station_data['status']}")

                # Check if we found any data
                if not result['schedule']:
                    # Check for "no data" messages
                    page_text = soup.get_text().lower()
                    if any(pattern in page_text for pattern in ['no schedule data', 'no data available', 'service not available']):
                        result['has_data'] = False
                        result['current_status'] = 'No schedule data available'
                        print("Found 'no data' message in page")
                    else:
                        print("No schedule data found but no explicit 'no data' message")
                        result['has_data'] = False
                        result['current_status'] = 'Unable to fetch schedule data'

                print(f"Final result: has_data={result['has_data']}, schedule_count={len(result['schedule'])}")
                print(f"Current station: {result['current_station']}, Next station: {result['next_station']}")
                
                return {
                    'status': 'success',
                    'message': 'Live status fetched successfully',
                    'data': result
                }
            
            print(f"HTTP request failed with status code: {response.status_code if response else 'No response'}")
            return {
                'status': 'error',
                'message': 'Failed to get live status - Service temporarily unavailable'
            }
                
        except Exception as e:
            print(f"Error getting live status: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f'Failed to get live status - {str(e)}'
            }

# Initialize Flask application
app = Flask(__name__)

# Configure Flask for production performance
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300  # 5 minutes cache
app.config['TEMPLATES_AUTO_RELOAD'] = False
app.config['JSON_SORT_KEYS'] = False  # Disable JSON key sorting for faster responses

# Initialize API instance with connection pooling
session = requests.Session()
session.verify = False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
api = ConfirmTktAPI()

# Add response compression
from flask_compress import Compress
Compress(app)

@app.after_request
def add_header(response):
    """Add headers to improve caching and performance"""
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'public, max-age=300'  # 5 minutes cache
    return response

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/live-status', methods=['GET', 'POST'])
@app.route('/api/live-status/<train_number>', methods=['GET', 'POST'])
def live_status(train_number=None):
    try:
        if request.method == 'POST':
            data = request.get_json()
            if data and 'train_number' in data:
                train_number = data['train_number']
        
        if not train_number:
            return jsonify({
                'status': 'error',
                'message': 'Train number is required'
            }), 400
        
        result = api.get_live_status(train_number)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get live status: {str(e)}'
        }), 500

# Update the schedule route to use caching
@app.route('/api/train-schedule', methods=['GET', 'POST'])
@app.route('/api/train-schedule/<train_number>', methods=['GET', 'POST'])
def train_schedule(train_number=None):
    try:
        # Get train number from request
        if request.method == 'POST':
            data = request.get_json()
            if data and 'train_number' in data:
                train_number = data['train_number']
        
        if not train_number:
            return jsonify({
                'status': 'error',
                'message': 'Train number is required'
            }), 400
        
        # Add response caching header
        response = make_response(jsonify(api.get_train_schedule(train_number)))
        response.headers['Cache-Control'] = 'public, max-age=3600'  # 1 hour cache
        return response
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get train schedule: {str(e)}'
        }), 500

@app.route('/api/pnr-status', methods=['GET', 'POST'])
@app.route('/api/pnr-status/<pnr_number>', methods=['GET', 'POST'])
def pnr_status(pnr_number=None):
    try:
        if request.method == 'POST':
            data = request.get_json()
            if data and 'pnr_number' in data:
                pnr_number = data['pnr_number']
        
        if not pnr_number:
            return jsonify({
                'status': 'error',
                'message': 'PNR number is required'
            }), 400
        
        result = api.get_pnr_status(pnr_number)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get PNR status: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Use production WSGI server if available
    try:
        from waitress import serve
        port = int(os.environ.get('PORT', 5001))
        print(f"Starting production server on port {port}")
        serve(app, host='0.0.0.0', port=port, threads=4)
    except ImportError:
        # Fallback to Flask development server
        port = int(os.environ.get('PORT', 5001))
        print(f"Starting development server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False) 