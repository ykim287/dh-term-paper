from typing import Any                                          # by yakuman
import scrapy
from scrapy.http import Response
from ..items import KaguyaItem
import re                                                       # imported for the remove_html_tags function on line 149

# This bot is written solely for scraping ilbe.com , whose search function outputs 10 results per page.
# Code modification would be required to support other websites.

# Initialize your scraping here ================================================== #
#
# Example: if you want to search pages 100 thru 115 of '강남역', 
#          you would set
#                           initial_index   = 100
#                           last_index      = 116       <= note how this 115+1!!!
#                           url_d           = 강남역


initial_index = 415
last_index = 1000                                                # once again, don't forget the last page checked is this value MINUS 1
url_a = 'https://www.ilbe.com'                                  # do not touch
url_b = '/search?docType=doc&searchType=title_content&page='    # do not touch
url_c = str(initial_index)                                      # do not touch
url_d = '&q='                                                   # do not touch
search_query = '강남역'             # you may touch


# Global variables that will be modified during execution ======================== #
index = initial_index                   # this value will increment during url collection
link_list = list()                      # stores urls
content_list = list()                   # stores content from web pages
phase_2 = False                         # boolean to denote transition from url collection to content collection
view_index = 0                          # this value will increment during content collection
items = KaguyaItem()                    # data's final resting place

# This is a class. Hope this helps.

class FlamenSpider(scrapy.Spider):
    
    # Declaring global values in the class so they can be used =================== #
    global url_a
    global url_b
    global url_c
    global url_d
    global search_query

    # Name of the spider ========================================================= #
    # In order to run it from the command line,
    #     go to kaguya-scraper\kaguyascraper and write:
    #                                                   scrapy crawl [name]
    # If you want to write the output to a file, write:
    #                                                   scrapy crawl [name] -o [filename].csv
    # There are other file extensions but just ask if need be.
    name = 'flamenco'
    
    # Starting point ============================================================= #
    # This is the first url the bot opens. If you've read up to this point you should know what link this string concatenation will form.
    start_urls = [
        url_a + url_b + url_c + url_d + search_query
    ]

    # This is the main function ================================================== #
    # HIGH-LEVEL EXPLANATION OF BOT LOGIC HERE
    # It's split into three steps that are enabled by ilbe.com's consistent structure, as mentioned previously
    # A search query outputs up to 1000 pages, each with 10 results.
    #
    # Step 1: the bot scrapes every search result page for 10 urls leading to posts
    # Step 2: the bot scrapes each individual url for its content
    # Step 3: the bot places the output from each step in alternating order, such that the output would look something like this:
    #               
    #                   [link 1] , [content of link 1] , [link 2] , [content of link 2] , [link 3] , [content of link 3]
    # Notes about output:
    #                       - commas are all deleted from content posts, such that commas delimit the boundary between content blocks and urls.
    #                       - certain posts on ilbe.com are members only, therefore the content for those posts will simply be '#####'

    def parse(self, response):

        # Declaring global values in the function so they can be used ============ #
        #
        global initial_index
        global index
        global last_index    
        global link_list
        global content_list
        global phase_2
        global view_index
        global items

        # Content collection ===================================================== #
        #
        if phase_2 == True:                                         # 
            content = response.css(".post-content").extract()       # extracting raw html
            if len(content) == 0 :                                  # if no content was extracted, that means it was probably a members' only page
                content = ['#####']                                 # therefore content would be null, so we write '#####' to it
            content_list.extend(content)                            #   note: 'ROBOTSTXT_OBEY' in settings.py has to be set to false to avoid runtime errors
            view_index = view_index + 1                             # once you're in the content collection phase, after this line,
                                                                    # you go straight to line 125

        # URL collection ========================================================= #
        #
        if index < last_index :                                     # this iterates thru search result pages,
                                                                    # meaning that once you've gone thru all the pages and gotten all your urls
                                                                    # this entire if block is skipped, go straight to the else, line 125
            
            link = response.css("li").xpath('//a[contains(@href, "/view/")]/@href').extract()   # a. manual inspection of search result pages
                                                                                                # shows that the 10 results' urls start with /view/
            link = list(dict.fromkeys(link))                                                    # b. this line deletes all duplicates from the list
            del link[-1]                                                                        # c. at the bottom of every page on ilbe, manual inspection
            del link[-1]                                                                        # showed there were two additional links starting with /view/
                                                                                                # therefore manually deleting the last two links in the list
                                                                                                # at every iteration fixes this issue
                                                                                                # THIS IS ONE OF THE REASONS THIS BOT IS SPECIFICALLY TAILORED TO
                                                                                                # ILBE.COM'S SEARCH RESULTS
            link_list.extend(link)

            # Having collected the urls from one search result page, we now go to the next.
            index = index + 1                                                                   # a. incrementing the index
            next_page =  url_a + url_b + str(index) + url_d + search_query                      # b. updating the next url to check
            if index <= last_index :                                                            # c. check to avoid leaving the desired page range
                
                yield response.follow(next_page, callback = self.parse)                         # instruction that tells the bot to open the next page,
                                                                                                # then go back to the start of the parse function, line 76
        
        
        # Content collection initialization/going to the next link ================ #
        #
        else :                                                                                  # once url collection is complete, this else block initiates the 
            phase_2 = True                                                                      # content collection by flipping the phase_2 boolean and making the bot
            if view_index <= ((last_index - initial_index) * 10 -1):                            # iterate through the url list in the content collection block at line 89
                yield response.follow("https://www.ilbe.com" + link_list[view_index], callback = self.parse)
       
       
        # Organizing data for storage ============================================ #
        # This block gets entered once everything has been scraped and stored in link_list and content_list.
        # 
            else :
                output = list()                                                                 # initializing final storage list
                for x in range(len(content_list)):                                             
                    html_cleaned = self.remove_html_tags(content_list[x])                       # a. wiping html tags from a piece of content for legibility
                    all_clean = html_cleaned.replace(",","")                                    # b. cleaning commas from content so content and links are clearly delineated
                    all_clean = html_cleaned.replace("\n","")                                   # c. cleaning newlines and tabs
                    all_clean = html_cleaned.replace("\t","")                                    
                    output.append('\n'+link_list[x])                                                 # d. appending links and content in alternating order
                    output.append(all_clean)                                                         # note: I also added a newline before every url which makes things more legible

                items['output'] = output                                                        # how scrapy likes to output stuff.
                yield items

    def remove_html_tags(self, text):                                                           # didn't write this function; Source:
        clean = re.compile('<.*?>')                                                             # https://medium.com/@jorlugaqui/how-to-strip-html-tags-from-a-string-in-python-7cb81a2bbf44
        return re.sub(clean, '', text)