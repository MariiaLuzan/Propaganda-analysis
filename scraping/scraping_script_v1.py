# %% [markdown]
# # Scraping the Broadcast News of Russian Channel One Web Site

# %%
import os.path
import csv
import scrapy
import requests
import pandas as pd
import dateparser
from scrapy.crawler import CrawlerProcess
from scrapy.exporters import CsvItemExporter

# Changing the maximum number of pandas dataframe rows shown to the screen to 20
# pd.options.display.max_rows = 120

# dateparser is used to parse date in different languages other than English (Russian in this case)
# https://stackoverflow.com/questions/41051389/pandas-parse-non-english-string-dates

# See the required dependencies at the end of this notebook


# %%
# Dependencies
# %pip install watermark
# %load_ext watermark
#%watermark -iv

# %% [markdown]
# Before digging into the actual scraping, let's see an example of connecting to the web site of *Channel One* and extract broadcast articles titles using a `Selector` object from the `scrapy` library using the `css` notation to access the `html` hierarchy (`xpath` notation could also be used).

# %%
# url = "https://www.1tv.ru/news"
# html = requests.get(url).content
# sel = scrapy.Selector(text=html)
# sel.css("article > a > div > div.title > h2::text").extract()


# %%
# url = "https://www.1tv.ru/news/2022-12-22/444010-vladimir_putin_ob_atakah_zapada_na_russkiy_mir_i_nashem_otvete"
# html = requests.get(url).content
# sel = scrapy.Selector(text=html)
# body = sel.xpath(
#            "//div[@class = 'editor text-block active' or @class = 'editor text-block']//text()"
#        ).extract()
# body

# %% [markdown]
# Some definitions before starting the explanation of the scraping process
# * the **offset** specifies where to start a page
#
# * the **limit** specifies the page size in the query about the request to the server

# %% [markdown]
# By looking at the Channel One News page, it is possible to recognize that it is a *partial infinite scrolling page*. At the time of writing, the web page shows the first 15 news (`limit = 15`, `offset = 0`; see the definition below) and the user should click *show more* to see more news (`limit = 15`, `offset = 15`)
#
# ![](https://drive.google.com/uc?export=view&id=17n5brqhux7GqAp9_n_F82Gx34Ze5YRyJ)
#
# After that the page scrolling infinitely as the user continues scrolling. In other words the browser requests the server to show additional 15 more entries (`offset = offset + 15`, `limit = 15`). The Occasionaly, the user is asked to click *show more* again.
#
# The Spider replicates this behavior sending requests to the server of showing 15 more additional entries
#
# The second part of the Spider is to enter inside each news article and scrape the data we are interested in (e.g. date, article title, article body, tags)

# %%
class Propaganda(scrapy.Spider):

    name = "propaganda"  # give whatever name
    allowed_domains = ["1tv.ru"]
    # the initial URL
    LIMIT = 15  # Specifying the page size in the query
    OFFSET = 345000  # Change this to set the beginning at a different point in time. OFFSET 0 --> Start from today 21 January 2023
    # OFFSET --> 1500 --> 25 December 2022
    OFFSET_INTERRUPT_AT = 360000
    start_urls = ["https://www.1tv.ru/news.js?limit=15&offset=" + str(OFFSET) + "?"]

    def parse(self, response):
        """Three actions
        1. Parsing the front web page 1tv.ru/news by saving locally the html file to scrape in order to collect broadcast urls
        2. For each of these urls the function call the function parse_pages() to scrape each broadcast
        3. Calling itself to scrape other broadcasts in other offsets
        """

        # Step 1. Connecting to the server and saving the html file of each offset locally
        path_folder = os.path.join(".\html_files")
        # e.g. loaded_offset_15.html
        html_file = "loaded_offset_" + str(self.OFFSET) + ".html"
        with open(
            os.path.join(path_folder, html_file), mode="w", encoding="utf-8"
        ) as f1:
            f1.write(response.css("html > body").extract()[0])

        # Opening the file and scraping the list of articles urls
        html_file_to_scrape = "./" + html_file
        with open(
            os.path.join(path_folder, html_file_to_scrape),
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as f2:
            page = f2.read()
            data = scrapy.Selector(text=str(page))
            url_broadcasts = data.css("article>a::attr(href)").extract()
            url_broadcasts = [url.replace("%5C'", "") for url in url_broadcasts]

            # Step 2. For each of these urls the function call the function parse_pages() to scrape each article
            for url in url_broadcasts:
                yield response.follow(url, callback=self.parse_pages)

        # to interrupt the spider, remove this when we are ready
        if self.OFFSET == self.OFFSET_INTERRUPT_AT:
            return None

        # Setting a new offset
        self.OFFSET += 15

        # Step 3. Calling itself to scrape other articles in other offsets
        new_request = (
            "https://www.1tv.ru/news.js?last_date=2023-01-04&limit="
            + str(self.LIMIT)
            + "&offset="
            + str(self.OFFSET)
            + "?"
        )  # the following url to scrape
        yield scrapy.Request(url=new_request, callback=self.parse)

    def parse_pages(self, response):
        """parsing each article page and collecting all the required data"""
        # Broadcast date
        date = response.css("div.date::text").extract()
        date_txt = "".join(date).replace("\xa0", " ")
        # Broadcast tags at the top of the page
        tags_top = response.xpath("//a[@class = 'itv-tag active']/text()").extract()
        # Broadcast title
        title = response.css("h1.title::text").extract()
        title_txt = "".join(title).replace("\xa0", " ")
        # Broadcast description
        body = response.xpath(
            "//div[@class = 'editor text-block active' or @class = 'editor text-block']//text()"
            # 20230128 Issue during testing  "//div[@class = 'editor text-block active']//p//text()"
            # Some news do not have the class 'editor text-block active' but only 'editor text-block';
            # Removed p because some news do not have the paragraph section
        ).extract()
        body_txt = "".join(body).replace("\xa0", " ")
        # Broadcast tags at the bottom of the page
        tags_bottom = (
            response.xpath(
                "//div[@class='itv-tag-list itv-tag-list--bottom itv-col-7 itv-col-offset-1']"
            )
            .css("a.itv-tag::text")
            .extract()
        )
        # Duration of the video
        video_duration = response.xpath(
            'head/meta[contains(@property,"video:duration")]/@content'
        ).extract()

        yield {
            "date": date_txt,
            "tags_top": tags_top,
            "title": title_txt,
            "url": response.url,
            "body": body_txt,
            "tags_bottom": tags_bottom,
            "video_duration_seconds": video_duration,
        }


# starting the Crawling and define export settings
process = CrawlerProcess(
    settings={
        "FEEDS": {
            "output_scraping.csv": {
                "format": "csv",
                "item_export_kwargs": {
                    "delimiter": "|",
                    "quotechar": '"',
                    "quoting": csv.QUOTE_ALL,
                },
            },
        },
    }
)

process.crawl(Propaganda)
process.start()


# %%
df = pd.read_csv(
    "output_scraping.csv",
    delimiter="|",
    date_parser=dateparser.parse,
    parse_dates=["date"],
)
df = df.sort_values(by="date", ascending=False)
df


# %%
df.head(100)

# %%
df.to_csv("output_scraping_cleaned.csv", sep="|", quoting=csv.QUOTE_ALL, quotechar='"')
