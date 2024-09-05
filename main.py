import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
import zipfile
from colorama import init, Fore, Style
import pyfiglet
import time
import sys

init(autoreset=True)

class Cloner:
    def __init__(self, url):
        self.url = url
        parsed_url = urllib.parse.urlparse(url)
        self.base_dir = os.path.join(os.getcwd(), f"cloned_{parsed_url.netloc}") 
        self.visited_assets = set()

    def clone_page(self):
        try:
            response = requests.get(self.url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                print(f"{Fore.YELLOW}Cloning in progress... ", end="", flush=True)
                self.show_progress()
                self.find_and_clone_assets(soup)
                self.update_asset_references(soup)
                self.save_page(soup)
                print(f"\n{Fore.GREEN}Page cloned successfully to {self.base_dir}")
            else:
                print(f"{Fore.RED}Error cloning page: Status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}Error cloning page: {e}")

    def find_and_clone_assets(self, soup):
        for tag in soup.find_all(['link', 'img', 'script']):
            attr = 'href' if tag.name == 'link' else 'src'
            asset_url = tag.get(attr)
            if asset_url:
                full_url = urllib.parse.urljoin(self.url, asset_url)
                if full_url not in self.visited_assets:
                    self.visited_assets.add(full_url)
                    self.clone_asset(full_url)

    def clone_asset(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                parsed_url_path = urllib.parse.urlparse(url).path
                sanitized_path = parsed_url_path.strip('/').replace(':', '_').replace('?', '_')
                path = os.path.join(self.base_dir, sanitized_path)

                os.makedirs(os.path.dirname(path), exist_ok=True)

                with open(path, 'wb') as file:
                    file.write(response.content)
            else:
                print(f"{Fore.YELLOW}Warning: Failed to clone asset {url}")
        except FileNotFoundError as e:
            print(f"{Fore.RED}FileNotFoundError: {e}. Skipping asset {url}.")
        except PermissionError as e:
            print(f"{Fore.RED}PermissionError: {e}. Check your folder permissions or path.")
        except requests.exceptions.RequestException as e:
            print(f"{Fore.YELLOW}Warning: Error cloning asset {url}: {e}")

    def update_asset_references(self, soup):
        for tag in soup.find_all(['link', 'img', 'script']):
            attr = 'href' if tag.name == 'link' else 'src'
            asset_url = tag.get(attr)
        
            if asset_url:
                full_url = urllib.parse.urljoin(self.url, asset_url)
                parsed_asset_url = urllib.parse.urlparse(full_url)
                if parsed_asset_url.path:  # Ensure the path is valid
                    try:
                        relative_path = os.path.relpath(os.path.join(self.base_dir, parsed_asset_url.path.lstrip('/')))
                        tag[attr] = relative_path
                    except ValueError:
                        print(f"Warning: Skipping invalid path for asset {asset_url}")

    def save_page(self, soup):
        os.makedirs(self.base_dir, exist_ok=True)
        with open(os.path.join(self.base_dir, 'index.html'), 'w', encoding='utf-8') as file:
            file.write(str(soup))

    def zip_cloned_page(self):
        zip_path = f"{self.base_dir}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(self.base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.base_dir)
                    zipf.write(file_path, arcname)
        print(f"{Fore.GREEN}Cloned page zipped successfully: {zip_path}")

    def show_progress(self):
        for i in range(10):
            time.sleep(0.2)
            sys.stdout.write(f"\rCloning in progress... {'\\' if i % 2 == 0 else '|'}")
            sys.stdout.flush()

def print_banner():
    banner = pyfiglet.figlet_format("WebSnap", font="slant", width=150)
    print(f"{Fore.CYAN}{Style.BRIGHT}{banner}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 50}")
    print(f"{Fore.YELLOW}Your Ultimate Web Page Cloning Tool")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 50}\n")

def main():
    print_banner()

    url = input(f"{Fore.YELLOW}Enter the URL of the page to clone: ")
    cloner = Cloner(url)
    cloner.clone_page()

    zip_option = input(f"{Fore.YELLOW}Do you want to zip the cloned page? (y/n): ").lower()
    if zip_option == 'y':
        cloner.zip_cloned_page()

    print(f"{Fore.GREEN}Operation completed successfully!")

if __name__ == "__main__":
    main()
