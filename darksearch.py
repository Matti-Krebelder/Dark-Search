#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DarkSearch - Lightweight dark web search tool
# Author: fsociety00

import argparse
import json
import os
import sys
import time
import re
import requests
import urllib.parse
from bs4 import BeautifulSoup
from multiprocessing import Pool, cpu_count
import random
import threading

# Terminal colors
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# ASCII Art frames
ASCII_FRAMES = [
    """
    ____             _    _____                     _     
   |  _ \\  __ _ _ __| | _/ ____|  ___  __ _ _ __ ___| |__  
   | | | |/ _` | '__| |/ \\___  \\ / _ \\/ _` | '__/ __| '_ \\ 
   | |_| | (_| | |  |   < ___) |  __/ (_| | | | (__| | | |
   |____/ \\__,_|_|  |_|\\_\\____/ \\___|\\__,_|_|  \\___|_| |_|
    """,
    """
    ____             _    _____                     _     
   |  _ \\  __ _ _ __| | _/ ____|  ___  __ _ _ __ ___| |_   
   | | | |/ _` | '__| |/ \\___  \\ / _ \\/ _` | '__/ __| '_ \\ 
   | |_| | (_| | |  |   < ___) |  __/ (_| | | | (__| | | |
   |____/ \\__,_|_|  |_|\\_\\____/ \\___|\\__,_|_|  \\___|_| |_|
    """,
    """
    ____             _    _____                     _     
   |  _ \\  __ _ _ __| | _/ ____|  ___  __ _ _ __ ___| | _  
   | | | |/ _` | '__| |/ \\___  \\ / _ \\/ _` | '__/ __| |/ /
   | |_| | (_| | |  |   < ___) |  __/ (_| | | | (__|   < 
   |____/ \\__,_|_|  |_|\\_\\____/ \\___|\\__,_|_|  \\___|_|\\_\\
    """
]

# Proxy and default headers
PROXY = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0',
    'Mozilla/5.0 (Android 10; Mobile; rv:91.0) Gecko/91.0 Firefox/91.0',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
]

# Search engines with their URLs (shortened list for lightweightness)
ENGINES = {
    "phobos": "http://phobosxilamwcg75xt22id7aywkzol6q6rfl2flipcqoc4e4ahima5id.onion",
    "onionland": "http://3bbad7fauom4d6sgppalyqddsqbf5u5p56b5k5uk2zxsy3d6ey2jobad.onion",
    "tor66": "http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion",
    "haystack": "http://haystak5njsmn2hqkewecpaxetahtwhsbsa64jom2k22z5afxhnpxfid.onion"
}

# Default configuration
DEFAULT_CONFIG = {
    "proxy": "127.0.0.1:9050",
    "max_results": 20,
    "active_engines": ["phobos", "onionland", "tor66", "haystack"],
    "threads": max(1, cpu_count() - 1)
}

CONFIG_FILE = "config.json"

# Function to load or create configuration
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            print(f"{Colors.RED}Error loading config, using defaults{Colors.ENDC}")
            return DEFAULT_CONFIG
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

# Function to save configuration
def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    print(f"{Colors.GREEN}Configuration saved to {CONFIG_FILE}{Colors.ENDC}")

# Animated ASCII art
def animate_ascii():
    i = 0
    while True:
        sys.stdout.write("\033[H\033[J")  # Clear screen
        print(f"{Colors.CYAN}{ASCII_FRAMES[i % len(ASCII_FRAMES)]}{Colors.ENDC}")
        print(f"{Colors.YELLOW}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.BOLD}DarkSearch - Tor Hidden Service Search Tool{Colors.ENDC}")
        print(f"{Colors.YELLOW}{'=' * 60}{Colors.ENDC}")
        sys.stdout.flush()
        time.sleep(0.3)
        i += 1
        if i > 100:  # Stop after a reasonable time
            break

# Random user agent
def random_headers():
    return {'User-Agent': random.choice(USER_AGENTS)}

# Function to clean text
def clean_text(text):
    return ' '.join(text.replace("\n", " ").split())

# Domain extraction
def get_domain(url):
    match = re.match(r"^https?://([a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,})", url)
    if match:
        return match.group(1)
    match = re.match(r"^https?://([a-zA-Z0-9\-\.]+\.onion)", url)
    if match:
        return match.group(1)
    return url

# Search function for different engines
def search_engine(engine_name, query, max_results):
    results = []
    
    try:
        if engine_name == "phobos":
            url = f"{ENGINES[engine_name]}/search?query={urllib.parse.quote(query)}&p=1"
            response = requests.get(url, proxies=PROXY, headers=random_headers(), timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for result in soup.find_all("div", class_="result"):
                link_elem = result.find("a", class_="titles")
                if link_elem:
                    name = clean_text(link_elem.get_text())
                    link = link_elem.get("href")
                    results.append({"name": name, "link": link, "engine": engine_name})
                    if len(results) >= max_results:
                        break
        
        elif engine_name == "onionland":
            url = f"{ENGINES[engine_name]}/search?q={urllib.parse.quote(query)}&page=1"
            response = requests.get(url, proxies=PROXY, headers=random_headers(), timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for result in soup.select('.result-block .title a'):
                if not result['href'].startswith('/ads/'):
                    name = clean_text(result.get_text())
                    link_param = urllib.parse.parse_qs(urllib.parse.urlparse(result['href']).query).get('l', [''])[0]
                    link = urllib.parse.unquote(urllib.parse.unquote(link_param))
                    results.append({"name": name, "link": link, "engine": engine_name})
                    if len(results) >= max_results:
                        break
        
        elif engine_name == "tor66":
            url = f"{ENGINES[engine_name]}/search?q={urllib.parse.quote(query)}&sorttype=rel&page=1"
            response = requests.get(url, proxies=PROXY, headers=random_headers(), timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for item in soup.find('hr').find_all_next('b'):
                if item.find('a'):
                    name = clean_text(item.find('a').get_text())
                    link = clean_text(item.find('a')['href'])
                    results.append({"name": name, "link": link, "engine": engine_name})
                    if len(results) >= max_results:
                        break
        
        elif engine_name == "haystack":
            url = f"{ENGINES[engine_name]}/?q={urllib.parse.quote(query)}&offset=0"
            response = requests.get(url, proxies=PROXY, headers=random_headers(), timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for result in soup.select(".result b a"):
                name = clean_text(result.get_text())
                link_param = urllib.parse.parse_qs(urllib.parse.urlparse(result['href']).query).get('url', [''])[0]
                link = link_param
                results.append({"name": name, "link": link, "engine": engine_name})
                if len(results) >= max_results:
                    break
    
    except Exception as e:
        print(f"{Colors.RED}Error with {engine_name}: {str(e)}{Colors.ENDC}")
    
    return results

# Function to search across multiple engines
def search_all(query, config):
    all_results = []
    
    engines = config["active_engines"]
    max_results = config["max_results"]
    threads = config["threads"]
    
    # Use multiprocessing for parallel search
    with Pool(threads) as pool:
        args = [(engine, query, max_results) for engine in engines]
        results = pool.starmap(search_engine, args)
    
    # Combine results
    for r in results:
        all_results.extend(r)
    
    return all_results

# Display search results with nice formatting
def display_results(results):
    if not results:
        print(f"{Colors.RED}No results found.{Colors.ENDC}")
        return
    
    print(f"\n{Colors.GREEN}Found {len(results)} results:{Colors.ENDC}\n")
    
    for i, result in enumerate(results, 1):
        print(f"{Colors.BOLD}{i:2d}.{Colors.ENDC} {Colors.CYAN}[{result['engine']}]{Colors.ENDC}")
        print(f"   {Colors.YELLOW}Title:{Colors.ENDC} {result['name']}")
        print(f"   {Colors.PURPLE}URL:{Colors.ENDC}   {result['link']}")
        print(f"   {Colors.BLUE}Domain:{Colors.ENDC} {get_domain(result['link'])}")
        print(f"{Colors.YELLOW}{'-' * 60}{Colors.ENDC}\n")

# Main menu function
def main_menu():
    config = load_config()
    
    # Start ASCII animation in a thread
    animation_thread = threading.Thread(target=animate_ascii)
    animation_thread.daemon = True
    animation_thread.start()
    
    # Wait for animation to display
    time.sleep(1)
    
    while True:
        # Stop animation effect by clearing screen
        sys.stdout.write("\033[H\033[J")
        
        # Display ASCII art
        print(f"{Colors.CYAN}{ASCII_FRAMES[0]}{Colors.ENDC}")
        print(f"{Colors.YELLOW}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.BOLD}DarkSearch - Tor Hidden Service Search Tool{Colors.ENDC}")
        print(f"{Colors.YELLOW}{'=' * 60}{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}Main Menu:{Colors.ENDC}")
        print(f"{Colors.GREEN}1. Search{Colors.ENDC}")
        print(f"{Colors.BLUE}2. Configure Search Engines{Colors.ENDC}")
        print(f"{Colors.PURPLE}3. Configure Settings{Colors.ENDC}")
        print(f"{Colors.RED}4. Quit{Colors.ENDC}")
        
        choice = input(f"\n{Colors.BOLD}Enter your choice (1-4): {Colors.ENDC}")
        
        if choice == '1':
            query = input(f"\n{Colors.BOLD}Enter search query: {Colors.ENDC}")
            if query.strip():
                print(f"\n{Colors.YELLOW}Searching for '{query}' across {len(config['active_engines'])} engines...{Colors.ENDC}")
                results = search_all(query, config)
                display_results(results)
                input(f"\n{Colors.GREEN}Press Enter to return to main menu...{Colors.ENDC}")
        
        elif choice == '2':
            configure_engines(config)
        
        elif choice == '3':
            configure_settings(config)
        
        elif choice == '4':
            print(f"\n{Colors.RED}Exiting DarkSearch...{Colors.ENDC}")
            sys.exit(0)

# Function to configure active search engines
def configure_engines(config):
    while True:
        sys.stdout.write("\033[H\033[J")  # Clear screen
        print(f"{Colors.BLUE}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.BOLD}Configure Search Engines{Colors.ENDC}")
        print(f"{Colors.BLUE}{'=' * 60}{Colors.ENDC}\n")
        
        print(f"{Colors.YELLOW}Available engines:{Colors.ENDC}\n")
        
        for i, engine in enumerate(ENGINES.keys(), 1):
            status = "Active" if engine in config["active_engines"] else "Inactive"
            color = Colors.GREEN if status == "Active" else Colors.RED
            print(f"{i}. {engine} - {color}{status}{Colors.ENDC}")
        
        print(f"\n{Colors.YELLOW}Options:{Colors.ENDC}")
        print("a. Toggle engine status")
        print("b. Enable all engines")
        print("c. Disable all engines")
        print("d. Return to main menu")
        
        choice = input(f"\n{Colors.BOLD}Enter your choice: {Colors.ENDC}")
        
        if choice == 'a':
            engine_num = input(f"\n{Colors.BOLD}Enter engine number to toggle: {Colors.ENDC}")
            try:
                engine_num = int(engine_num)
                if 1 <= engine_num <= len(ENGINES):
                    engine_name = list(ENGINES.keys())[engine_num-1]
                    if engine_name in config["active_engines"]:
                        config["active_engines"].remove(engine_name)
                        print(f"{Colors.RED}Disabled {engine_name}{Colors.ENDC}")
                    else:
                        config["active_engines"].append(engine_name)
                        print(f"{Colors.GREEN}Enabled {engine_name}{Colors.ENDC}")
                    save_config(config)
                    time.sleep(1)
            except ValueError:
                print(f"{Colors.RED}Invalid input{Colors.ENDC}")
                time.sleep(1)
        
        elif choice == 'b':
            config["active_engines"] = list(ENGINES.keys())
            save_config(config)
            print(f"{Colors.GREEN}All engines enabled{Colors.ENDC}")
            time.sleep(1)
        
        elif choice == 'c':
            config["active_engines"] = []
            save_config(config)
            print(f"{Colors.RED}All engines disabled{Colors.ENDC}")
            time.sleep(1)
        
        elif choice == 'd':
            return

# Function to configure general settings
def configure_settings(config):
    while True:
        sys.stdout.write("\033[H\033[J")  # Clear screen
        print(f"{Colors.PURPLE}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.BOLD}Configure Settings{Colors.ENDC}")
        print(f"{Colors.PURPLE}{'=' * 60}{Colors.ENDC}\n")
        
        print(f"{Colors.YELLOW}Current settings:{Colors.ENDC}\n")
        print(f"1. Proxy: {config['proxy']}")
        print(f"2. Max results per engine: {config['max_results']}")
        print(f"3. Number of threads: {config['threads']}")
        print(f"\n{Colors.YELLOW}Options:{Colors.ENDC}")
        print("a. Change proxy")
        print("b. Change max results")
        print("c. Change thread count")
        print("d. Reset to defaults")
        print("e. Return to main menu")
        
        choice = input(f"\n{Colors.BOLD}Enter your choice: {Colors.ENDC}")
        
        if choice == 'a':
            proxy = input(f"\n{Colors.BOLD}Enter new proxy (format: host:port): {Colors.ENDC}")
            if proxy.strip():
                config["proxy"] = proxy
                global PROXY
                PROXY = {'http': f'socks5h://{proxy}', 'https': f'socks5h://{proxy}'}
                save_config(config)
                print(f"{Colors.GREEN}Proxy updated{Colors.ENDC}")
                time.sleep(1)
        
        elif choice == 'b':
            try:
                max_results = int(input(f"\n{Colors.BOLD}Enter max results per engine: {Colors.ENDC}"))
                if max_results > 0:
                    config["max_results"] = max_results
                    save_config(config)
                    print(f"{Colors.GREEN}Max results updated{Colors.ENDC}")
                    time.sleep(1)
                else:
                    print(f"{Colors.RED}Invalid input{Colors.ENDC}")
                    time.sleep(1)
            except ValueError:
                print(f"{Colors.RED}Invalid input{Colors.ENDC}")
                time.sleep(1)
        
        elif choice == 'c':
            try:
                threads = int(input(f"\n{Colors.BOLD}Enter number of threads: {Colors.ENDC}"))
                if 1 <= threads <= cpu_count():
                    config["threads"] = threads
                    save_config(config)
                    print(f"{Colors.GREEN}Thread count updated{Colors.ENDC}")
                    time.sleep(1)
                else:
                    print(f"{Colors.RED}Invalid input. Must be between 1 and {cpu_count()}{Colors.ENDC}")
                    time.sleep(1)
            except ValueError:
                print(f"{Colors.RED}Invalid input{Colors.ENDC}")
                time.sleep(1)
        
        elif choice == 'd':
            config = DEFAULT_CONFIG.copy()
            save_config(config)
            print(f"{Colors.GREEN}Settings reset to defaults{Colors.ENDC}")
            time.sleep(1)
        
        elif choice == 'e':
            return

# Entry point
if __name__ == "__main__":
    # Handle command line arguments for direct search
    parser = argparse.ArgumentParser(description="DarkSearch - Tor Hidden Service Search Tool")
    parser.add_argument("-q", "--query", help="Search query")
    args = parser.parse_args()
    
    try:
        # Test Tor connection
        test_url = "https://check.torproject.org/"
        requests.get(test_url, proxies=PROXY, timeout=15)
    except Exception as e:
        print(f"{Colors.RED}Error: Cannot connect to Tor. Make sure Tor is running on {PROXY['http'].split('/')[-1]}{Colors.ENDC}")
        print(f"{Colors.RED}Error details: {str(e)}{Colors.ENDC}")
        sys.exit(1)
    
    # If query provided via command line, do direct search
    if args.query:
        config = load_config()
        print(f"{Colors.YELLOW}Searching for '{args.query}' across {len(config['active_engines'])} engines...{Colors.ENDC}")
        results = search_all(args.query, config)
        display_results(results)
    else:
        # Run interactive menu
        try:
            main_menu()
        except KeyboardInterrupt:
            print(f"\n{Colors.RED}Exiting DarkSearch...{Colors.ENDC}")
            sys.exit(0)
