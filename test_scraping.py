#!/usr/bin/env python3
"""
Test script to debug ConfirmTkt scraping issues
"""

import requests
from bs4 import BeautifulSoup
import json

def test_confirmtkt_access():
    """Test if we can access ConfirmTkt website"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        # Test main page
        print("Testing main page access...")
        response = requests.get('https://www.confirmtkt.com', headers=headers, timeout=10)
        print(f"Main page status: {response.status_code}")
        print(f"Content length: {len(response.content)}")
        
        # Test live status page
        print("\nTesting live status page...")
        live_url = 'https://www.confirmtkt.com/train-running-status/15032'
        response = requests.get(live_url, headers=headers, timeout=10)
        print(f"Live status page status: {response.status_code}")
        print(f"Content length: {len(response.content)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"Page title: {soup.title.text if soup.title else 'No title'}")
            
            # Look for data in scripts
            scripts_with_data = 0
            for script in soup.find_all('script'):
                if script.string and ('var data' in script.string or 'currentStn' in script.string):
                    scripts_with_data += 1
                    print(f"Found script with data: {script.string[:100]}...")
            
            print(f"Scripts with data found: {scripts_with_data}")
        
        # Test train schedule page
        print("\nTesting train schedule page...")
        schedule_url = 'https://www.confirmtkt.com/train-schedule/12307'
        response = requests.get(schedule_url, headers=headers, timeout=10)
        print(f"Schedule page status: {response.status_code}")
        print(f"Content length: {len(response.content)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all('table')
            print(f"Tables found: {len(tables)}")
            
        # Test PNR status page
        print("\nTesting PNR status page...")
        pnr_url = 'https://www.confirmtkt.com/pnr-status/1234567890'
        response = requests.get(pnr_url, headers=headers, timeout=10)
        print(f"PNR page status: {response.status_code}")
        print(f"Content length: {len(response.content)}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

def test_with_proxy():
    """Test with one of our proxies"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    proxy = {
        'http': 'http://189.240.60.172:9090',
        'https': 'http://189.240.60.172:9090'
    }
    
    try:
        print("\nTesting with proxy...")
        response = requests.get('https://www.confirmtkt.com/train-running-status/15032', 
                              headers=headers, proxies=proxy, timeout=10, verify=False)
        print(f"Proxy request status: {response.status_code}")
        print(f"Content length: {len(response.content)}")
        
    except Exception as e:
        print(f"Proxy error: {str(e)}")

if __name__ == '__main__':
    print("=== ConfirmTkt Scraping Test ===")
    test_confirmtkt_access()
    test_with_proxy() 