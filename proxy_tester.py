#!/usr/bin/env python3
"""
Enhanced Proxy Tester - Tests proxies with response time tracking and detailed status
"""

import requests
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from datetime import datetime
import urllib3
import sys
from tabulate import tabulate
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ProxyTester:
    def __init__(self):
        self.all_proxies = []
        self.working_proxies = []
        self.failed_proxies = []
        self.test_urls = [
            "https://www.confirmtkt.com/train-running-status/15665",
            "https://httpbin.org/ip",
            "https://www.google.com",
            "https://www.example.com"
        ]
        self.timeout = 10
        self.max_workers = 50
        self.lock = threading.Lock()
        self.progress = 0
        self.start_time = None
        
    def load_all_proxies(self):
        """Load proxies from files with status display"""
        print("\n📂 Loading proxy lists...")
        
        proxy_files = [
            'working_proxies.txt',
            'working_proxies_detailed.json'
        ]
        
        all_proxies = set()
        
        for file_name in proxy_files:
            try:
                if file_name.endswith('.json'):
                    with open(file_name, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and 'working_proxies' in data:
                            for proxy_info in data['working_proxies']:
                                if isinstance(proxy_info, dict) and 'proxy' in proxy_info:
                                    all_proxies.add(proxy_info['proxy'])
                else:
                with open(file_name, 'r') as f:
                    proxies = [line.strip() for line in f if line.strip()]
                    all_proxies.update(proxies)
                print(f"✅ Loaded proxies from {file_name}")
            except FileNotFoundError:
                print(f"⚠️  {file_name} not found")
            except Exception as e:
                print(f"❌ Error loading {file_name}: {e}")
        
        self.all_proxies = list(all_proxies)
        print(f"\n📊 Total unique proxies to test: {len(self.all_proxies)}")
        return len(self.all_proxies)
    
    def update_progress(self):
        """Update and display progress"""
        self.progress += 1
        total = len(self.all_proxies)
        elapsed = time.time() - self.start_time
        rate = self.progress / elapsed if elapsed > 0 else 0
        eta = (total - self.progress) / rate if rate > 0 else 0
        
        sys.stdout.write('\r')
        sys.stdout.write(f"Progress: [{self.progress}/{total}] {self.progress/total*100:.1f}% | "
                        f"Working: {len(self.working_proxies)} | "
                        f"ETA: {eta/60:.1f}min")
        sys.stdout.flush()
    
    def test_single_proxy(self, proxy):
        """Test a single proxy with detailed timing"""
        proxy_dict = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }
        
        test_url = random.choice(self.test_urls)
        result = {
            'proxy': proxy,
            'status': 'failed',
            'test_url': test_url,
            'error': None,
            'timings': {}
        }
        
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            # Measure connection time
            start_connect = time.time()
            response = session.get(
                test_url,
                proxies=proxy_dict,
                timeout=self.timeout,
                verify=False,
                allow_redirects=True
            )
            end_request = time.time()
            
            result['timings'] = {
                'connect': round(end_request - start_connect, 3),
                'total': round(end_request - start_connect, 3)
            }
            
            if response.status_code == 200:
                result.update({
                    'status': 'working',
                    'status_code': response.status_code,
                    'content_length': len(response.content)
                })
                with self.lock:
                    self.working_proxies.append(result)
            else:
                result['error'] = f"HTTP {response.status_code}"
                with self.lock:
                    self.failed_proxies.append(result)
                
        except requests.exceptions.Timeout:
            result['error'] = 'Timeout'
        except requests.exceptions.ConnectionError:
            result['error'] = 'Connection Error'
        except Exception as e:
            result['error'] = str(e)[:100]
        
        if result['error']:
            with self.lock:
                self.failed_proxies.append(result)
        
        with self.lock:
            self.update_progress()
        
        return result
    
    def test_all_proxies(self):
        """Test all proxies with real-time status updates"""
        print("\n🚀 Starting proxy tests...")
        print(f"⚙️  Using {self.max_workers} concurrent workers")
        print(f"⏱️  Timeout: {self.timeout} seconds per proxy")
        print("=" * 60)
        
        self.start_time = time.time()
        self.progress = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.test_single_proxy, proxy) 
                      for proxy in self.all_proxies]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"\n❌ Error in proxy test: {e}")
        
        print("\n\n✅ Testing complete!")
        return len(self.working_proxies)

    def display_results(self):
        """Display detailed results in a formatted table"""
        if not self.working_proxies:
            print("\n❌ No working proxies found!")
            return
        
        # Sort by total response time
        self.working_proxies.sort(key=lambda x: x['timings']['total'])
        
        # Prepare table data
        headers = ["Proxy", "Response Time", "Connect Time", "Status"]
        table_data = []
        
        for proxy in self.working_proxies[:20]:  # Show top 20
            table_data.append([
                proxy['proxy'],
                f"{proxy['timings']['total']}s",
                f"{proxy['timings']['connect']}s",
                "✅ Working" if proxy['status'] == 'working' else "❌ Failed"
            ])
        
        print("\n🏆 Top 20 Fastest Working Proxies:")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Calculate and display statistics
        total_proxies = len(self.all_proxies)
        working_count = len(self.working_proxies)
        success_rate = (working_count / total_proxies) * 100 if total_proxies > 0 else 0
        
        response_times = [p['timings']['total'] for p in self.working_proxies]
        avg_time = sum(response_times) / len(response_times) if response_times else 0
        
        print("\n📊 Statistics:")
        print(f"Total Proxies Tested: {total_proxies}")
        print(f"Working Proxies: {working_count}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Average Response Time: {avg_time:.3f}s")
        
        # Save results
        self.save_results()

    def save_results(self):
        """Save detailed results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save simple list of working proxies
        with open('working_proxies.txt', 'w') as f:
            for proxy in self.working_proxies:
                f.write(f"{proxy['proxy']}\n")
        
        # Save detailed results
        results = {
            'timestamp': timestamp,
            'total_tested': len(self.all_proxies),
            'working_count': len(self.working_proxies),
            'success_rate': (len(self.working_proxies) / len(self.all_proxies)) * 100,
            'working_proxies': self.working_proxies,
            'failed_proxies': self.failed_proxies
        }
        
        with open('working_proxies_detailed.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n💾 Results saved to:")
        print("   - working_proxies.txt")
        print("   - working_proxies_detailed.json")

def main():
    tester = ProxyTester()
    if tester.load_all_proxies() > 0:
        tester.test_all_proxies()
        tester.display_results()
    else:
        print("❌ No proxies to test!")

if __name__ == "__main__":
    main() 