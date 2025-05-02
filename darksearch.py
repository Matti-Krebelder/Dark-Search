#!/usr/bin/python3

import argparse
import csv
import math
import re
import time
import os
import sys
import signal
from datetime import datetime
from functools import reduce
from random import choice
from multiprocessing import Pool, cpu_count, current_process, freeze_support
from tqdm import tqdm

import requests
import urllib.parse as urlparse
from urllib.parse import parse_qs
from urllib.parse import quote
from urllib.parse import unquote
from bs4 import BeautifulSoup
from urllib3.exceptions import ProtocolError

# Import for colored output
try:
    from colorama import init, Fore, Back, Style
    # Initialize colorama for cross-platform colored output
    init(autoreset=True)
    COLOR_SUPPORT = True
except ImportError:
    # Create dummy color constants if colorama is not available
    class DummyFore:
        def __getattr__(self, name):
            return ""
    Fore = DummyFore()
    Style = DummyFore()
    COLOR_SUPPORT = False

# ASCII Art for the application
ASCII_ART = f"""
{Fore.CYAN} ____             _      ____                      _     
{Fore.CYAN}|  _ \  __ _ _ __| | __ / ___|  ___  __ _ _ __ ___| |__  
{Fore.BLUE}| | | |/ _` | '__| |/ / \___ \ / _ \/ _` | '__/ __| '_ \ 
{Fore.BLUE}| |_| | (_| | |  |   <   ___) |  __/ (_| | | | (__| | | |
{Fore.MAGENTA}|____/ \__,_|_|  |_|\_\ |____/ \___|\__,_|_|  \___|_| |_|
{Fore.MAGENTA} 
{Style.RESET_ALL}
{Fore.YELLOW}═══════════════════════════════════════════════════════════════════════════════
{Fore.GREEN}  Dark Web Search Tool - by fsociety00
{Fore.YELLOW}═══════════════════════════════════════════════════════════════════════════════
{Style.RESET_ALL}
"""

ENGINES = {
    "ahmia": "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion",
    "darksearchio": "http://darksearch.io",
    "onionland": "http://3bbad7fauom4d6sgppalyqddsqbf5u5p56b5k5uk2zxsy3d6ey2jobad.onion",
    "notevil": "http://hss3uro2hsxfogfq.onion",
    "darksearchenginer": "http://l4rsciqnpzdndt2llgjx3luvnxip7vbyj6k6nmdy4xs77tx6gkd24ead.onion",
    "phobos": "http://phobosxilamwcg75xt22id7aywkzol6q6rfl2flipcqoc4e4ahima5id.onion",
    "onionsearchserver": "http://3fzh7yuupdfyjhwt3ugzqqof6ulbcl27ecev33knxe3u7goi3vfn2qqd.onion",
    "torgle": "http://no6m4wzdexe3auiupv2zwif7rm6qwxcyhslkcnzisxgeiw6pvjsgafad.onion",
    "tor66": "http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion",
    "haystack": "http://haystak5njsmn2hqkewecpaxetahtwhsbsa64jom2k22z5afxhnpxfid.onion",
}

# Engines categorization and status
ENGINE_STATUS = {name: {"active": True, "category": "General"} for name in ENGINES.keys()}
# Additional categories
ENGINE_STATUS["darksearchio"]["category"] = "Clearnet"
ENGINE_STATUS["phobos"]["category"] = "Popular"
ENGINE_STATUS["tor66"]["category"] = "Popular"
ENGINE_STATUS["haystack"]["category"] = "Popular"

desktop_agents = [
    'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0',  # Tor Browser for Windows and Linux
    'Mozilla/5.0 (Android 10; Mobile; rv:91.0) Gecko/91.0 Firefox/91.0',  # Tor Browser for Android
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) '
    'AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'
]

supported_engines = ENGINES

available_csv_fields = [
    "engine",
    "name",
    "link",
    "domain"
]

# Global variables for use in interactive mode
interactive_mode = False
results_cache = []

# Signal handler for clean exit
def signal_handler(sig, frame):
    print(f"\n{Fore.YELLOW}Search interrupted by user. Exiting...{Style.RESET_ALL}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print the application header."""
    clear_screen()
    print(ASCII_ART)

def print_menu():
    """Print the interactive menu."""
    print(f"\n{Fore.CYAN}╔══════════════════════════════════════╗")
    print(f"{Fore.CYAN}║{Fore.WHITE}           MAIN MENU                {Fore.CYAN}║")
    print(f"{Fore.CYAN}╠══════════════════════════════════════╣")
    print(f"{Fore.CYAN}║{Fore.WHITE} 1. Search                          {Fore.CYAN}║")
    print(f"{Fore.CYAN}║{Fore.WHITE} 2. Configure Search Engines        {Fore.CYAN}║") 
    print(f"{Fore.CYAN}║{Fore.WHITE} 3. Set Proxy                       {Fore.CYAN}║")
    print(f"{Fore.CYAN}║{Fore.WHITE} 4. Help                            {Fore.CYAN}║")
    print(f"{Fore.CYAN}║{Fore.WHITE} 5. Exit                            {Fore.CYAN}║")
    print(f"{Fore.CYAN}╚══════════════════════════════════════╝{Style.RESET_ALL}")

def print_engine_menu():
    """Print the engine configuration menu."""
    print_header()
    print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════╗")
    print(f"{Fore.CYAN}║{Fore.WHITE}             SEARCH ENGINE CONFIGURATION              {Fore.CYAN}║")
    print(f"{Fore.CYAN}╠══════════════════════════════════════════════════════════╣")
    
    categories = set(info["category"] for info in ENGINE_STATUS.values())
    
    for category in sorted(categories):
        print(f"{Fore.CYAN}║ {Fore.YELLOW}{category.upper()}:                                             {Fore.CYAN}║")
        
        for i, (engine, info) in enumerate(ENGINE_STATUS.items()):
            if info["category"] == category:
                status = f"{Fore.GREEN}[✓]" if info["active"] else f"{Fore.RED}[✗]"
                print(f"{Fore.CYAN}║ {status} {i+1:2d}. {Fore.WHITE}{engine:<20}{Fore.CYAN}                         ║")
    
    print(f"{Fore.CYAN}╠══════════════════════════════════════════════════════════╣")
    print(f"{Fore.CYAN}║{Fore.WHITE} A. Toggle All On                                      {Fore.CYAN}║")
    print(f"{Fore.CYAN}║{Fore.WHITE} N. Toggle All Off                                     {Fore.CYAN}║")
    print(f"{Fore.CYAN}║{Fore.WHITE} R. Return to Main Menu                                {Fore.CYAN}║")
    print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
    
    print(f"\n{Fore.WHITE}Enter the number of an engine to toggle its status, or choose an option:{Style.RESET_ALL}")

def handle_engine_menu():
    """Handle the engine configuration menu."""
    while True:
        print_engine_menu()
        choice = input(f"{Fore.GREEN}> {Style.RESET_ALL}").strip().lower()
        
        if choice == 'r':
            return
        elif choice == 'a':
            for engine in ENGINE_STATUS:
                ENGINE_STATUS[engine]["active"] = True
        elif choice == 'n':
            for engine in ENGINE_STATUS:
                ENGINE_STATUS[engine]["active"] = False
        elif choice.isdigit() and 1 <= int(choice) <= len(ENGINE_STATUS):
            engine = list(ENGINE_STATUS.keys())[int(choice)-1]
            ENGINE_STATUS[engine]["active"] = not ENGINE_STATUS[engine]["active"]
        else:
            print(f"{Fore.RED}Invalid option. Please try again.{Style.RESET_ALL}")
            time.sleep(1)

def print_help():
    """Display help information."""
    print_header()
    print(f"{Fore.YELLOW}╔══════════════════════════════════════════════════════════════════════╗")
    print(f"{Fore.YELLOW}║{Fore.WHITE}                             HELP                               {Fore.YELLOW}║")
    print(f"{Fore.YELLOW}╠══════════════════════════════════════════════════════════════════════╣")
    print(f"{Fore.YELLOW}║{Fore.WHITE} This tool searches across multiple Tor search engines.          {Fore.YELLOW}║")
    print(f"{Fore.YELLOW}║{Fore.WHITE}                                                                {Fore.YELLOW}║")
    print(f"{Fore.YELLOW}║{Fore.WHITE} Usage:                                                         {Fore.YELLOW}║")
    print(f"{Fore.YELLOW}║{Fore.WHITE} 1. Ensure Tor is running (default: localhost:9050)             {Fore.YELLOW}║")
    print(f"{Fore.YELLOW}║{Fore.WHITE} 2. Enter your search query                                     {Fore.YELLOW}║")
    print(f"{Fore.YELLOW}║{Fore.WHITE} 3. View results in real-time                                   {Fore.YELLOW}║")
    print(f"{Fore.YELLOW}║{Fore.WHITE} 4. Results are saved to a CSV file                             {Fore.YELLOW}║")
    print(f"{Fore.YELLOW}║{Fore.WHITE}                                                                {Fore.YELLOW}║")
    print(f"{Fore.YELLOW}║{Fore.WHITE} DISCLAIMER:                                                    {Fore.YELLOW}║")
    print(f"{Fore.YELLOW}║{Fore.RED} This tool is for educational purposes only. The creators are not {Fore.YELLOW}║")
    print(f"{Fore.YELLOW}║{Fore.RED} responsible for any misuse of this software.                     {Fore.YELLOW}║")
    print(f"{Fore.YELLOW}║{Fore.RED} Accessing illegal content is strictly prohibited.                {Fore.YELLOW}║")
    print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
    
    input(f"\n{Fore.CYAN}Press Enter to return to the main menu...{Style.RESET_ALL}")

def random_headers():
    return {'User-Agent': choice(desktop_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}

def clear(toclear):
    str = toclear.replace("\n", " ")
    str = ' '.join(str.split())
    return str

def get_parameter(url, parameter_name):
    parsed = urlparse.urlparse(url)
    return parse_qs(parsed.query)[parameter_name][0]

def get_proc_pos():
    return (current_process()._identity[0]) - 1 if hasattr(current_process(), '_identity') and current_process()._identity else 0

def get_tqdm_desc(e_name, pos):
    if COLOR_SUPPORT:
        return f"{Fore.CYAN}{e_name:<20}{Style.RESET_ALL} (#%d)" % pos
    else:
        return "%20s (#%d)" % (e_name, pos)

def ahmia(searchstr, proxies):
    results = []
    ahmia_url = supported_engines['ahmia'] + "/search/?q={}"

    try:
        pos = get_proc_pos()
        with tqdm(total=1, initial=0, desc=get_tqdm_desc("Ahmia", pos), position=pos) as progress_bar:
            response = requests.get(ahmia_url.format(quote(searchstr)), proxies=proxies, headers=random_headers(), timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            results = link_finder("ahmia", soup)
            progress_bar.update()
    except (requests.exceptions.RequestException, ProtocolError) as e:
        if not interactive_mode:
            print(f"{Fore.YELLOW}[!] Ahmia search engine is not available.{Style.RESET_ALL}")
    
    return results

def darksearchio(searchstr, proxies):
    results = []
    darksearchio_url = supported_engines['darksearchio'] + "/api/search?query={}&page={}"
    max_nb_page = 5  # Reduced for better performance in interactive mode
    if args.limit != 0:
        max_nb_page = args.limit

    try:
        with requests.Session() as s:
            s.proxies = proxies
            s.headers = random_headers()
            resp = s.get(darksearchio_url.format(quote(searchstr), 1), timeout=10)

            page_number = 1
            if resp.status_code == 200:
                resp = resp.json()
                if 'last_page' in resp:
                    page_number = resp['last_page']
                if page_number > max_nb_page:
                    page_number = max_nb_page
            else:
                return []

            pos = get_proc_pos()
            with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("DarkSearch (.io)", pos), position=pos) \
                    as progress_bar:

                results = link_finder("darksearchio", resp['data'])
                progress_bar.update()

                for n in range(2, page_number + 1):
                    resp = s.get(darksearchio_url.format(quote(searchstr), n), timeout=10)
                    if resp.status_code == 200:
                        resp = resp.json()
                        results = results + link_finder("darksearchio", resp['data'])
                        progress_bar.update()
                    else:
                        progress_bar.update()
    except (requests.exceptions.RequestException, ProtocolError, ValueError) as e:
        if not interactive_mode:
            print(f"{Fore.YELLOW}[!] DarkSearch.io search engine is not available.{Style.RESET_ALL}")
    
    return results

def onionland(searchstr, proxies):
    results = []
    onionlandv3_url = supported_engines['onionland'] + "/search?q={}&page={}"
    max_nb_page = 3  # Reduced for better performance in interactive mode
    if args.limit != 0:
        max_nb_page = args.limit

    try:
        with requests.Session() as s:
            s.proxies = proxies
            s.headers = random_headers()

            resp = s.get(onionlandv3_url.format(quote(searchstr), 1), timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            page_number = 1
            for i in soup.find_all('div', attrs={"class": "search-status"}):
                div = i.find('div', attrs={'class': "col-sm-12"})
                if div:
                    approx_re = re.match(r"About ([,0-9]+) result(.*)", clear(div.get_text()))
                    if approx_re is not None:
                        nb_res = int((approx_re.group(1)).replace(",", ""))
                        results_per_page = 19
                        page_number = math.ceil(nb_res / results_per_page)
                        if page_number > max_nb_page:
                            page_number = max_nb_page

            pos = get_proc_pos()
            with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("OnionLand", pos), position=pos) as progress_bar:
                results = link_finder("onionland", soup)
                progress_bar.update()

                for n in range(2, page_number + 1):
                    resp = s.get(onionlandv3_url.format(quote(searchstr), n), timeout=15)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    ret = link_finder("onionland", soup)
                    if len(ret) == 0:
                        break
                    results = results + ret
                    progress_bar.update()
    except (requests.exceptions.RequestException, ProtocolError) as e:
        if not interactive_mode:
            print(f"{Fore.YELLOW}[!] OnionLand search engine is not available.{Style.RESET_ALL}")
    
    return results

def notevil(searchstr, proxies):
    results = []
    notevil_url1 = supported_engines['notevil'] + "/index.php?q={}"
    notevil_url2 = supported_engines['notevil'] + "/index.php?q={}&hostLimit=20&start={}&numRows={}&template=0"
    max_nb_page = 3  # Reduced for better performance in interactive mode
    if args.limit != 0:
        max_nb_page = args.limit

    try:
        # Do not use requests.Session() here (by experience less results would be got)
        req = requests.get(notevil_url1.format(quote(searchstr)), proxies=proxies, headers=random_headers(), timeout=15)
        soup = BeautifulSoup(req.text, 'html.parser')

        page_number = 1
        last_div = soup.find("div", attrs={"style": "text-align:center"})
        if last_div:
            last_div = last_div.find("div", attrs={"style": "text-align:center"})
            if last_div is not None:
                for i in last_div.find_all("a"):
                    page_number = int(i.get_text())
                if page_number > max_nb_page:
                    page_number = max_nb_page

        pos = get_proc_pos()
        with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("Not Evil", pos), position=pos) as progress_bar:
            num_rows = 20
            results = link_finder("notevil", soup)
            progress_bar.update()

            for n in range(2, page_number + 1):
                start = (int(n - 1) * num_rows)
                req = requests.get(notevil_url2.format(quote(searchstr), start, num_rows),
                                   proxies=proxies,
                                   headers=random_headers(),
                                   timeout=15)
                soup = BeautifulSoup(req.text, 'html.parser')
                results = results + link_finder("notevil", soup)
                progress_bar.update()
                time.sleep(0.5)
    except (requests.exceptions.RequestException, ProtocolError) as e:
        if not interactive_mode:
            print(f"{Fore.YELLOW}[!] Not Evil search engine is not available.{Style.RESET_ALL}")
    
    return results

def darksearchenginer(searchstr, proxies):
    results = []
    darksearchenginer_url = supported_engines['darksearchenginer']
    max_nb_page = 3  # Reduced for better performance in interactive mode
    if args.limit != 0:
        max_nb_page = args.limit
    page_number = 1

    try:
        with requests.Session() as s:
            s.proxies = proxies
            s.headers = random_headers()

            # Note that this search engine is very likely to timeout
            resp = s.post(darksearchenginer_url, data={"search[keyword]": searchstr, "page": page_number}, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            pages_input = soup.find_all("input", attrs={"name": "page"})
            for i in pages_input:
                page_number = int(i['value'])
                if page_number > max_nb_page:
                    page_number = max_nb_page

            pos = get_proc_pos()
            with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("Dark Search Enginer", pos), position=pos) \
                    as progress_bar:

                results = link_finder("darksearchenginer", soup)
                progress_bar.update()

                for n in range(2, page_number + 1):
                    resp = s.post(darksearchenginer_url, data={"search[keyword]": searchstr, "page": str(n)}, timeout=15)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    results = results + link_finder("darksearchenginer", soup)
                    progress_bar.update()
    except (requests.exceptions.RequestException, ProtocolError) as e:
        if not interactive_mode:
            print(f"{Fore.YELLOW}[!] Dark Search Enginer is not available.{Style.RESET_ALL}")
    
    return results

def phobos(searchstr, proxies):
    results = []
    phobos_url = supported_engines['phobos'] + "/search?query={}&p={}"
    max_nb_page = 3  # Reduced for better performance in interactive mode
    if args.limit != 0:
        max_nb_page = args.limit

    try:
        with requests.Session() as s:
            s.proxies = proxies
            s.headers = random_headers()

            resp = s.get(phobos_url.format(quote(searchstr), 1), timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            page_number = 1
            pages_div = soup.find("div", attrs={"class": "pages"})
            if pages_div:
                pages = pages_div.find_all('a')
                if pages:
                    for i in pages:
                        page_number = int(i.get_text())
                    if page_number > max_nb_page:
                        page_number = max_nb_page

            pos = get_proc_pos()
            with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("Phobos", pos), position=pos) as progress_bar:
                results = link_finder("phobos", soup)
                progress_bar.update()

                for n in range(2, page_number + 1):
                    resp = s.get(phobos_url.format(quote(searchstr), n), timeout=15)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    results = results + link_finder("phobos", soup)
                    progress_bar.update()
    except (requests.exceptions.RequestException, ProtocolError) as e:
        if not interactive_mode:
            print(f"{Fore.YELLOW}[!] Phobos search engine is not available.{Style.RESET_ALL}")
    
    return results

def onionsearchserver(searchstr, proxies):
    results = []
    onionsearchserver_url1 = supported_engines['onionsearchserver'] + "/oss/"
    onionsearchserver_url2 = None
    results_per_page = 10
    max_nb_page = 3  # Reduced for better performance in interactive mode
    if args.limit != 0:
        max_nb_page = args.limit

    try:
        with requests.Session() as s:
            s.proxies = proxies
            s.headers = random_headers()

            resp = s.get(onionsearchserver_url1, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for i in soup.find_all('iframe', attrs={"style": "display:none;"}):
                onionsearchserver_url2 = i['src'] + "{}&page={}"

            if onionsearchserver_url2 is None:
                return results

            resp = s.get(onionsearchserver_url2.format(quote(searchstr), 1), timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            page_number = 1
            pages = soup.find_all("div", attrs={"class": "osscmnrdr ossnumfound"})
            if pages and not str(pages[0].get_text()).startswith("No"):
                total_results = float(str.split(clear(pages[0].get_text()))[0])
                page_number = math.ceil(total_results / results_per_page)
                if page_number > max_nb_page:
                    page_number = max_nb_page

            pos = get_proc_pos()
            with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("Onion Search Server", pos), position=pos) \
                    as progress_bar:

                results = link_finder("onionsearchserver", soup)
                progress_bar.update()

                for n in range(2, page_number + 1):
                    resp = s.get(onionsearchserver_url2.format(quote(searchstr), n), timeout=15)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    results = results + link_finder("onionsearchserver", soup)
                    progress_bar.update()
    except (requests.exceptions.RequestException, ProtocolError) as e:
        if not interactive_mode:
            print(f"{Fore.YELLOW}[!] Onion Search Server is not available.{Style.RESET_ALL}")
    
    return results

def torgle(searchstr, proxies):
    results = []
    torgle_url = supported_engines['torgle'] + "/search.php?term={}"

    try:
        pos = get_proc_pos()
        with tqdm(total=1, initial=0, desc=get_tqdm_desc("Torgle", pos), position=pos) as progress_bar:
            response = requests.get(torgle_url.format(quote(searchstr)), proxies=proxies, headers=random_headers(), timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            results = link_finder("torgle", soup)
            progress_bar.update()
    except (requests.exceptions.RequestException, ProtocolError) as e:
        if not interactive_mode:
            print(f"{Fore.YELLOW}[!] Torgle search engine is not available.{Style.RESET_ALL}")
    
    return results

def tor66(searchstr, proxies):
    results = []
    tor66_url = supported_engines['tor66'] + "/search?q={}&sorttype=rel&page={}"
    max_nb_page = 3  # Reduced for better performance in interactive mode
    if args.limit != 0:
        max_nb_page = args.limit

    try:
        with requests.Session() as s:
            s.proxies = proxies
            s.headers = random_headers()

            resp = s.get(tor66_url.format(quote(searchstr), 1), timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            page_number = 1
            pagination = soup.find('div', attrs={'class': 'pagination'})
            if pagination:
                for a in pagination.find_all('a'):
                    try:
                        page = int(a.get_text())
                        if page > page_number:
                            page_number = page
                    except ValueError:
                        pass
                
                if page_number > max_nb_page:
                    page_number = max_nb_page

            pos = get_proc_pos()
            with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("Tor66", pos), position=pos) as progress_bar:
                results = link_finder("tor66", soup)
                progress_bar.update()

                for n in range(2, page_number + 1):
                    resp = s.get(tor66_url.format(quote(searchstr), n), timeout=15)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    results = results + link_finder("tor66", soup)
                    progress_bar.update()
    except (requests.exceptions.RequestException, ProtocolError) as e:
        if not interactive_mode:
            print(f"{Fore.YELLOW}[!] Tor66 search engine is not available.{Style.RESET_ALL}")
    
    return results

def haystack(searchstr, proxies):
    results = []
    haystack_url = supported_engines['haystack'] + "/search?q={}&offset={}"
    results_per_page = 10
    max_nb_page = 3  # Reduced for better performance in interactive mode
    if args.limit != 0:
        max_nb_page = args.limit

    try:
        with requests.Session() as s:
            s.proxies = proxies
            s.headers = random_headers()

            resp = s.get(haystack_url.format(quote(searchstr), 0), timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            page_number = 1
            total_results_div = soup.find('div', attrs={'class': 'alert'})
            if total_results_div:
                results_text = total_results_div.get_text()
                match = re.search(r'Found (\d+) results', results_text)
                if match:
                    total_results = int(match.group(1))
                    page_number = math.ceil(total_results / results_per_page)
                    if page_number > max_nb_page:
                        page_number = max_nb_page

            pos = get_proc_pos()
            with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("Haystack", pos), position=pos) as progress_bar:
                results = link_finder("haystack", soup)
                progress_bar.update()

                for n in range(1, page_number):
                    offset = n * results_per_page
                    resp = s.get(haystack_url.format(quote(searchstr), offset), timeout=15)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    results = results + link_finder("haystack", soup)
                    progress_bar.update()
    except (requests.exceptions.RequestException, ProtocolError) as e:
        if not interactive_mode:
            print(f"{Fore.YELLOW}[!] Haystack search engine is not available.{Style.RESET_ALL}")
    
    return results

def link_finder(engine_name, soup_object):
    """
    Extract links from search engine results based on engine-specific HTML structure
    Returns a list of dictionaries containing search results
    """
    results = []
    
    if engine_name == "ahmia":
        for div in soup_object.find_all('li', attrs={'class': 'result'}):
            title_element = div.find('h4')
            if title_element:
                title = clear(title_element.get_text())
                link_element = div.find('a', href=True)
                if link_element:
                    link = link_element['href']
                    if link.startswith('/'):
                        link = supported_engines['ahmia'] + link
                    
                    # Extract domain from link
                    domain = urlparse.urlparse(link).netloc
                    
                    results.append({
                        'engine': engine_name,
                        'name': title,
                        'link': link,
                        'domain': domain
                    })

    elif engine_name == "darksearchio":
        for item in soup_object:
            if 'title' in item and 'link' in item:
                title = clear(item['title'])
                link = item['link']
                domain = urlparse.urlparse(link).netloc
                
                results.append({
                    'engine': engine_name,
                    'name': title,
                    'link': link,
                    'domain': domain
                })

    elif engine_name == "onionland":
        for div in soup_object.find_all('div', attrs={'class': 'result-block'}):
            title_element = div.find('h4')
            if title_element:
                title = clear(title_element.get_text())
                link_element = div.find('a', href=True)
                if link_element:
                    link = link_element['href']
                    domain = urlparse.urlparse(link).netloc
                    
                    results.append({
                        'engine': engine_name,
                        'name': title,
                        'link': link,
                        'domain': domain
                    })

    elif engine_name == "notevil":
        for div in soup_object.find_all('div', attrs={'class': 'result'}):
            title_element = div.find('h4')
            if title_element:
                title = clear(title_element.get_text())
                link_element = div.find('a', href=True)
                if link_element:
                    link = link_element['href']
                    domain = urlparse.urlparse(link).netloc
                    
                    results.append({
                        'engine': engine_name,
                        'name': title,
                        'link': link,
                        'domain': domain
                    })

    elif engine_name == "darksearchenginer":
        for div in soup_object.find_all('div', attrs={'class': 'dark_result'}):
            title_element = div.find('h2')
            if title_element:
                title = clear(title_element.get_text())
                link_element = div.find('a', href=True)
                if link_element:
                    link = link_element['href']
                    domain = urlparse.urlparse(link).netloc
                    
                    results.append({
                        'engine': engine_name,
                        'name': title,
                        'link': link,
                        'domain': domain
                    })

    elif engine_name == "phobos":
        for div in soup_object.find_all('div', attrs={'class': 'result'}):
            title_element = div.find('h5')
            if title_element:
                title = clear(title_element.get_text())
                link_element = div.find('a', href=True)
                if link_element:
                    link = link_element['href']
                    domain = urlparse.urlparse(link).netloc
                    
                    results.append({
                        'engine': engine_name,
                        'name': title,
                        'link': link,
                        'domain': domain
                    })

    elif engine_name == "onionsearchserver":
        for div in soup_object.find_all('div', attrs={'class': 'osscmnrdr ossresult'}):
            title_element = div.find('a')
            if title_element:
                title = clear(title_element.get_text())
                link = title_element['href']
                domain = urlparse.urlparse(link).netloc
                
                results.append({
                    'engine': engine_name,
                    'name': title,
                    'link': link,
                    'domain': domain
                })

    elif engine_name == "torgle":
        for div in soup_object.find_all('div', attrs={'class': 'result'}):
            title_element = div.find('h3')
            if title_element:
                title = clear(title_element.get_text())
                link_element = div.find('a', href=True)
                if link_element:
                    link = link_element['href']
                    domain = urlparse.urlparse(link).netloc
                    
                    results.append({
                        'engine': engine_name,
                        'name': title,
                        'link': link,
                        'domain': domain
                    })

    elif engine_name == "tor66":
        for div in soup_object.find_all('div', attrs={'class': 'post'}):
            title_element = div.find('h5')
            if title_element:
                title = clear(title_element.get_text())
                link_element = div.find('a', href=True)
                if link_element:
                    link = link_element['href']
                    domain = urlparse.urlparse(link).netloc
                    
                    results.append({
                        'engine': engine_name,
                        'name': title,
                        'link': link,
                        'domain': domain
                    })

    elif engine_name == "haystack":
        for div in soup_object.find_all('div', attrs={'class': 'result'}):
            title_element = div.find('h3')
            if title_element:
                title = clear(title_element.get_text())
                link_element = div.find('a', href=True)
                if link_element:
                    link = link_element['href']
                    domain = urlparse.urlparse(link).netloc
                    
                    results.append({
                        'engine': engine_name,
                        'name': title,
                        'link': link,
                        'domain': domain
                    })

    return results

def search_thread(engine_func, searchstr, proxies):
    """Function to execute a search engine query in a thread"""
    if ENGINE_STATUS[engine_func.__name__]["active"]:
        try:
            return engine_func(searchstr, proxies)
        except Exception as e:
            if not interactive_mode:
                print(f"{Fore.RED}Error searching with {engine_func.__name__}: {str(e)}{Style.RESET_ALL}")
    return []

def perform_search(searchstr, proxies):
    """
    Execute search across all active engines, using multiprocessing for parallel execution
    Returns a list of dictionaries containing search results
    """
    global results_cache
    
    start_time = time.time()
    selected_engines = []
    
    # Get list of active engines
    for engine_name, info in ENGINE_STATUS.items():
        if info["active"]:
            if engine_name == "ahmia":
                selected_engines.append(ahmia)
            elif engine_name == "darksearchio":
                selected_engines.append(darksearchio)
            elif engine_name == "onionland":
                selected_engines.append(onionland)
            elif engine_name == "notevil":
                selected_engines.append(notevil)
            elif engine_name == "darksearchenginer":
                selected_engines.append(darksearchenginer)
            elif engine_name == "phobos":
                selected_engines.append(phobos)
            elif engine_name == "onionsearchserver":
                selected_engines.append(onionsearchserver)
            elif engine_name == "torgle":
                selected_engines.append(torgle)
            elif engine_name == "tor66":
                selected_engines.append(tor66)
            elif engine_name == "haystack":
                selected_engines.append(haystack)
    
    # Check if any engines are selected
    if len(selected_engines) == 0:
        print(f"{Fore.RED}No search engines selected. Please enable at least one engine.{Style.RESET_ALL}")
        return []
    
    # Determine number of processes to use
    if not interactive_mode:
        process_count = min(len(selected_engines), cpu_count())
        print(f"{Fore.GREEN}[+] Starting search across {len(selected_engines)} engines using {process_count} processes...{Style.RESET_ALL}")
    
        # Create a pool of processes
        with Pool(processes=process_count) as pool:
            # Create a list of tasks
            tasks = [(engine, searchstr, proxies) for engine in selected_engines]
            
            # Execute the tasks in parallel and collect results
            results = pool.starmap(search_thread, tasks)
            
            # Flatten the list of results
            all_results = [item for sublist in results for item in sublist]
    else:
        all_results = []
        for engine in selected_engines:
            results = search_thread(engine, searchstr, proxies)
            all_results.extend(results)
    
    # Save results in cache for interactive mode
    results_cache = all_results
    
    # Calculate search time
    search_time = time.time() - start_time
    
    # Print summary statistics
    unique_domains = len(set(item['domain'] for item in all_results))
    print(f"\n{Fore.GREEN}[+] Search completed in {search_time:.2f} seconds")
    print(f"[+] Found {len(all_results)} results from {unique_domains} unique domains across {len(selected_engines)} engines{Style.RESET_ALL}")
    
    return all_results

def save_results_to_csv(results, search_query, output_file=None):
    """Save search results to a CSV file"""
    if not results:
        print(f"{Fore.YELLOW}[!] No results to save.{Style.RESET_ALL}")
        return None
    
    # Generate filename if not provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_query = re.sub(r'[^\w\s-]', '', search_query).replace(' ', '_')
        output_file = f"torsearch_{sanitized_query}_{timestamp}.csv"
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=available_csv_fields)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"{Fore.GREEN}[+] Results saved to: {output_file}{Style.RESET_ALL}")
        return output_file
    except Exception as e:
        print(f"{Fore.RED}[!] Error saving results: {str(e)}{Style.RESET_ALL}")
        return None

def display_results(results, max_displayed=20):
    """Display search results in the terminal"""
    if not results:
        print(f"{Fore.YELLOW}No results found.{Style.RESET_ALL}")
        return
    
    # Group results by domain
    results_by_domain = {}
    for result in results:
        domain = result.get('domain', 'unknown')
        if domain not in results_by_domain:
            results_by_domain[domain] = []
        results_by_domain[domain].append(result)
    
    # Sort domains by number of results (descending)
    sorted_domains = sorted(results_by_domain.keys(), 
                           key=lambda k: len(results_by_domain[k]), 
                           reverse=True)
    
    # Display results grouped by domain
    print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗")
    print(f"{Fore.CYAN}║{Fore.WHITE}                     SEARCH RESULTS                      {Fore.CYAN}║")
    print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
    
    displayed_count = 0
    for domain in sorted_domains:
        if displayed_count >= max_displayed:
            remaining = len(results) - displayed_count
            print(f"\n{Fore.YELLOW}... and {remaining} more results not shown. Export to CSV for complete results.{Style.RESET_ALL}")
            break
        
        domain_results = results_by_domain[domain]
        print(f"\n{Fore.MAGENTA}Domain: {Fore.WHITE}{domain} {Fore.YELLOW}({len(domain_results)} results){Style.RESET_ALL}")
        
        # Display a subset of results for each domain
        for i, result in enumerate(domain_results[:3]):  # Show max 3 results per domain
            if displayed_count >= max_displayed:
                break
            
            print(f"{Fore.GREEN}{i+1}. {Fore.WHITE}{result['name']}")
            print(f"   {Fore.BLUE}{result['link']}")
            print(f"   {Fore.YELLOW}Source: {result['engine']}{Style.RESET_ALL}")
            displayed_count += 1

def set_proxy():
    """Configure proxy settings interactively"""
    print_header()
    print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════╗")
    print(f"{Fore.CYAN}║{Fore.WHITE}                 PROXY CONFIGURATION                  {Fore.CYAN}║")
    print(f"{Fore.CYAN}╠══════════════════════════════════════════════════════════╣")
    print(f"{Fore.CYAN}║{Fore.WHITE} Enter your SOCKS proxy in format: host:port           {Fore.CYAN}║")
    print(f"{Fore.CYAN}║{Fore.WHITE} Default is localhost:9050 (Tor's default SOCKS port)  {Fore.CYAN}║")
    print(f"{Fore.CYAN}║{Fore.WHITE} Leave empty to use the default                        {Fore.CYAN}║")
    print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
    
    proxy_input = input(f"\n{Fore.GREEN}Enter proxy (default: localhost:9050): {Style.RESET_ALL}").strip()
    
    if not proxy_input:
        proxy_host = "localhost"
        proxy_port = 9050
    else:
        try:
            proxy_host, proxy_port = proxy_input.split(':')
            proxy_port = int(proxy_port)
        except ValueError:
            print(f"{Fore.RED}Invalid proxy format. Using default (localhost:9050).{Style.RESET_ALL}")
            proxy_host = "localhost"
            proxy_port = 9050
    
    proxies = {
        'http': f'socks5h://{proxy_host}:{proxy_port}',
        'https': f'socks5h://{proxy_host}:{proxy_port}'
    }
    
    # Test the proxy
    print(f"\n{Fore.YELLOW}Testing proxy connection...{Style.RESET_ALL}")
    try:
        test_url = "http://httpbin.org/ip"
        response = requests.get(test_url, proxies=proxies, timeout=10)
        if response.status_code == 200:
            print(f"{Fore.GREEN}Proxy connection successful!{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Proxy connection failed with status code: {response.status_code}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Proxy connection failed: {str(e)}{Style.RESET_ALL}")
    
    input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
    return proxies

def interactive_mode_loop():
    """Main loop for interactive mode"""
    global interactive_mode
    interactive_mode = True
    
    # Default proxy settings
    proxies = {
        'http': 'socks5h://localhost:9050',
        'https': 'socks5h://localhost:9050'
    }
    
    while True:
        print_header()
        print_menu()
        
        choice = input(f"\n{Fore.GREEN}Enter your choice (1-5): {Style.RESET_ALL}").strip()
        
        if choice == '1':  # Search
            print_header()
            print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════╗")
            print(f"{Fore.CYAN}║{Fore.WHITE}                   SEARCH QUERY                       {Fore.CYAN}║")
            print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
            
            search_query = input(f"\n{Fore.GREEN}Enter your search query: {Style.RESET_ALL}").strip()
            
            if search_query:
                results = perform_search(search_query, proxies)
                
                if results:
                    display_results(results)
                    
                    save_option = input(f"\n{Fore.GREEN}Save results to CSV? (y/n): {Style.RESET_ALL}").strip().lower()
                    if save_option == 'y':
                        save_results_to_csv(results, search_query)
                
                input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
        
        elif choice == '2':  # Configure Search Engines
            handle_engine_menu()
        
        elif choice == '3':  # Set Proxy
            proxies = set_proxy()
        
        elif choice == '4':  # Help
            print_help()
        
        elif choice == '5':  # Exit
            print(f"\n{Fore.YELLOW}Exiting...{Style.RESET_ALL}")
            sys.exit(0)
        
        else:
            print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
            time.sleep(1)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='TorSEEK - Dark Web Search Tool')
    parser.add_argument('-s', '--search', help='Search query')
    parser.add_argument('-e', '--engines', help='Comma-separated list of search engines to use')
    parser.add_argument('-p', '--proxy', help='SOCKS proxy to use (default: localhost:9050)')
    parser.add_argument('-o', '--output', help='Output file for results (CSV format)')
    parser.add_argument('-l', '--limit', type=int, default=0, help='Limit number of pages per search engine')
    parser.add_argument('-i', '--interactive', action='store_true', help='Run in interactive mode')
    
    global args
    args = parser.parse_args()
    
    # Run in interactive mode if specified or if no search query is provided
    if args.interactive or not args.search:
        interactive_mode_loop()
        return
    
    # Configure proxy
    if args.proxy:
        try:
            proxy_host, proxy_port = args.proxy.split(':')
            proxy_port = int(proxy_port)
        except ValueError:
            print(f"{Fore.RED}[!] Invalid proxy format. Using default (localhost:9050).{Style.RESET_ALL}")
            proxy_host = "localhost"
            proxy_port = 9050
    else:
        proxy_host = "localhost"
        proxy_port = 9050
    
    proxies = {
        'http': f'socks5h://{proxy_host}:{proxy_port}',
        'https': f'socks5h://{proxy_host}:{proxy_port}'
    }
    
    # Configure search engines
    if args.engines:
        engine_list = [e.strip().lower() for e in args.engines.split(',')]
        for engine in ENGINE_STATUS:
            ENGINE_STATUS[engine]["active"] = engine in engine_list
    
    # Print banner
    print(ASCII_ART)
    
    # Execute search
    print(f"{Fore.GREEN}[+] Searching for: {args.search}{Style.RESET_ALL}")
    results = perform_search(args.search, proxies)
    
    # Save results to CSV
    if results:
        save_results_to_csv(results, args.search, args.output)

if __name__ == "__main__":
    freeze_support()
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Search interrupted by user. Exiting...{Style.RESET_ALL}")
        sys.exit(0)
