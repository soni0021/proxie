#!/usr/bin/env python3
"""
Test script to verify exact scraping from ConfirmTkt URLs
"""

import requests
from bs4 import BeautifulSoup
import json
import re

def test_live_status():
    """Test live status scraping for train 22462"""
    url = "https://www.confirmtkt.com/train-running-status/22462"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Live Status URL: {url}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract train name
            title = soup.find('title')
            print(f"Page Title: {title.text if title else 'No title'}")
            
            # Look for SHRI SHAKTI EXP
            train_info = soup.find(string=lambda text: text and 'SHRI SHAKTI EXP' in text)
            if train_info:
                print(f"Train Info Found: {train_info.strip()}")
            
            # Look for "Yet to start from"
            status_text = soup.find(string=lambda text: text and 'Yet to start from' in text)
            if status_text:
                print(f"Status: {status_text.strip()}")
            
            # Look for last updated
            last_updated = soup.find(string=lambda text: text and 'Last Updated:' in text)
            if last_updated:
                print(f"Last Updated: {last_updated.strip()}")
            
            # Find tables
            tables = soup.find_all('table')
            print(f"Tables found: {len(tables)}")
            
            if tables:
                table = tables[0]
                rows = table.find_all('tr')
                print(f"Table rows: {len(rows)}")
                
                for i, row in enumerate(rows[:3]):  # Show first 3 rows
                    cols = row.find_all(['td', 'th'])
                    row_data = [col.text.strip() for col in cols]
                    print(f"Row {i}: {row_data}")
        
        print("-" * 50)
        
    except Exception as e:
        print(f"Error testing live status: {str(e)}")

def test_train_schedule():
    """Test train schedule scraping for train 22461"""
    url = "https://www.confirmtkt.com/train-schedule/22461"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Train Schedule URL: {url}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract train name
            header = soup.find('h1')
            print(f"Header: {header.text if header else 'No header'}")
            
            # Look for train route info
            route_info = soup.find(string=lambda text: text and 'New Delhi to Mata Vaishno Devi Katra' in text)
            if route_info:
                print(f"Route: {route_info.strip()}")
            
            # Look for running days
            running_days = soup.find(string=lambda text: text and 'Running Days' in text)
            if running_days:
                print(f"Running Days: {running_days.strip()}")
            
            # Find tables
            tables = soup.find_all('table')
            print(f"Tables found: {len(tables)}")
            
            if tables:
                table = tables[0]
                rows = table.find_all('tr')
                print(f"Table rows: {len(rows)}")
                
                # Show header row
                if rows:
                    header_row = rows[0]
                    headers = [th.text.strip() for th in header_row.find_all(['th', 'td'])]
                    print(f"Headers: {headers}")
                
                # Show first few data rows
                for i, row in enumerate(rows[1:4]):  # Show first 3 data rows
                    cols = row.find_all(['td', 'th'])
                    row_data = [col.text.strip() for col in cols]
                    print(f"Row {i+1}: {row_data}")
        
        print("-" * 50)
        
    except Exception as e:
        print(f"Error testing train schedule: {str(e)}")

def test_pnr_status():
    """Test PNR status scraping"""
    url = "https://www.confirmtkt.com/pnr-status?pnr=1234567889"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"PNR Status URL: {url}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract page content
            page_text = soup.get_text()
            print(f"Page contains 'ConfirmTkt': {'ConfirmTkt' in page_text}")
            print(f"Page contains 'PNR': {'PNR' in page_text}")
            print(f"Page contains 'Invalid': {'Invalid' in page_text.lower()}")
            
            # Look for any train numbers
            train_numbers = re.findall(r'\b\d{5}\b', page_text)
            if train_numbers:
                print(f"Train numbers found: {train_numbers}")
            
            # Look for tables
            tables = soup.find_all('table')
            print(f"Tables found: {len(tables)}")
            
            # Show page title
            title = soup.find('title')
            print(f"Page Title: {title.text if title else 'No title'}")
            
            # Show first 500 characters of text content
            print(f"Page content (first 500 chars): {page_text[:500]}")
        
        print("-" * 50)
        
    except Exception as e:
        print(f"Error testing PNR status: {str(e)}")

if __name__ == '__main__':
    print("=== Testing Exact ConfirmTkt Scraping ===")
    test_live_status()
    test_train_schedule()
    test_pnr_status() 