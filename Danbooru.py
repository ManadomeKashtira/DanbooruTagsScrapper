import requests
import time
import os
import json
from datetime import datetime
import base64

class DanbooruTagScraper:
    BASE_URL = "https://danbooru.donmai.us/tags.json"
    HEADERS = {"User-Agent": "TagScraper/1.0"}
    TAG_CATEGORIES = {
        0: "general",
        1: "artist",
        3: "copyright",
        4: "character",
        5: "meta"
    }

    def __init__(self, filename, category=None, min_post_count=0, order="name",
                 include_metadata=False, delay=0.5, username=None, api_key=None):
        self.filename = filename if filename.endswith(".txt") else filename + ".txt"
        self.statefile = self.filename + ".state.json"
        self.category = category
        self.min_post_count = min_post_count
        self.order = order
        self.include_metadata = include_metadata
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

        if username and api_key:
            auth_str = base64.b64encode(f"{username}:{api_key}".encode()).decode()
            self.session.headers["Authorization"] = f"Basic {auth_str}"

        self.tags = []
        self.seen = set()
        self.page = 1
        self._load_progress()

    def _load_progress(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                self.tags = [line.strip() for line in f if line.strip()]
                self.seen = {line.split("\t")[0] if "\t" in line else line for line in self.tags}
        if os.path.exists(self.statefile):
            with open(self.statefile, "r", encoding="utf-8") as f:
                self.page = json.load(f).get("page", 1)

    def _save_progress(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write("\n".join(self.tags))
        with open(self.statefile, "w", encoding="utf-8") as f:
            json.dump({"page": self.page, "timestamp": datetime.now().isoformat()}, f)

    def run(self):
        print(f"▶ Starting scrape: category={self.category}, order={self.order}, min_posts={self.min_post_count}")
        try:
            while True:
                params = {
                    "limit": 1000,
                    "page": self.page,
                    "search[order]": self.order
                }
                if self.category is not None:
                    params["search[category]"] = self.category
                if self.min_post_count > 0:
                    params["search[post_count]"] = f">={self.min_post_count}"

                resp = self.session.get(self.BASE_URL, params=params, timeout=20)

                if resp.status_code == 429:
                    print("⏳ Rate limited, backing off...")
                    time.sleep(self.delay * 4)
                    continue

                resp.raise_for_status()
                data = resp.json()
                if not data:
                    print("✅ Done — no more tags.")
                    break

                new_count = 0
                for tag in data:
                    name = tag.get("name", "").strip()
                    if not name or name in self.seen:
                        continue

                    if self.include_metadata:
                        count = tag.get("post_count", 0)
                        cat = self.TAG_CATEGORIES.get(tag.get("category", -1), "unknown")
                        line = f"{name}\t{count}\t{cat}"
                    else:
                        line = name

                    self.tags.append(line)
                    self.seen.add(name)
                    new_count += 1

                print(f"📄 Page {self.page}: added {new_count} new tags (total {len(self.tags)})")
                self._save_progress()
                self.page += 1
                time.sleep(self.delay)

        except KeyboardInterrupt:
            print("\n🛑 Interrupted, saving...")
            self._save_progress()
        finally:
            if os.path.exists(self.statefile):
                os.remove(self.statefile)
            print(f"💾 Saved {len(self.tags)} tags to {self.filename}")


def scrape_all_tags(filename, delay=0.5, include_metadata=False, username=None, api_key=None):
    """Scrape ALL categories at once (like tion.py but saves to TXT)."""
    filename = filename if filename.endswith(".txt") else filename + ".txt"
    session = requests.Session()
    session.headers.update({"User-Agent": "TagScraper/1.0"})

    if username and api_key:
        auth_str = base64.b64encode(f"{username}:{api_key}".encode()).decode()
        session.headers["Authorization"] = f"Basic {auth_str}"

    tags = []
    seen = set()
    page = 1

    while True:
        print(f"📥 Fetching page {page}...")
        params = {"limit": 1000, "page": page, "search[order]": "count"}
        try:
            r = session.get(DanbooruTagScraper.BASE_URL, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"⚠️ Error fetching page {page}: {e}")
            break

        if not data:
            print("✅ No more data.")
            break

        for tag in data:
            name = tag.get("name", "").strip()
            if not name or name in seen:
                continue
            if include_metadata:
                count = tag.get("post_count", 0)
                cat = DanbooruTagScraper.TAG_CATEGORIES.get(tag.get("category", -1), "unknown")
                line = f"{name}\t{count}\t{cat}"
            else:
                line = name
            tags.append(line)
            seen.add(name)

        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(tags))

        page += 1
        time.sleep(delay)

    print(f"💾 Saved {len(tags)} tags to {filename}")


def main():
    print("🏷️  Danbooru Tag Scraper")
    print("=" * 40)

    filename = input(" Enter filename (without .txt): ").strip()
    if not filename:
        print("❌ Filename required!")
        return

    print("\n📂 Tag categories:")
    print("   0 = general tags")
    print("   1 = artist tags")
    print("   3 = copyright tags")
    print("   4 = character tags")
    print("   5 = meta tags")
    print("   all = ALL categories")

    category_input = input("\n Enter category (default: 0): ").strip() or "0"
    if category_input.lower() == "all":
        category = "all"
    else:
        try:
            category = int(category_input)
            if category not in [0, 1, 3, 4, 5]:
                print("❌ Invalid category!")
                return
        except ValueError:
            print("❌ Invalid input!")
            return

    print("\n Sort order:")
    print("   newest = newest tags first")
    print("   name = alphabetical order")
    print("   count = by post count (most popular first)")

    order_input = input("\n🔄 Enter sort order (default: name): ").strip() or "name"
    if order_input not in ["newest", "name", "count"]:
        print("❌ Invalid order!")
        return

    try:
        min_posts = int(input("\n Minimum post count (default: 0): ").strip() or "0")
    except ValueError:
        print("❌ Invalid number!")
        return

    try:
        delay = float(input("\n Delay between requests (default: 0.5): ").strip() or "0.5")
    except ValueError:
        print("❌ Invalid number!")
        return

    metadata_input = input("\n Include post count & category info? (y/N): ").strip().lower()
    include_metadata = metadata_input in ['y', 'yes']

    
    if category == "all":
        scrape_all_tags(filename, delay, include_metadata)
    else:
        scraper = DanbooruTagScraper(
            filename=filename,
            category=category,
            min_post_count=min_posts,
            order=order_input,
            include_metadata=include_metadata,
            delay=delay
        )
        scraper.run()


if __name__ == "__main__":
    main()
