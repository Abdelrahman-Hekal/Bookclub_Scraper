
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
import pandas as pd
import time
import unidecode
import csv
import sys
import numpy as np

def initialize_bot():

    # Setting up chrome driver for the bot
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    chrome_service = ChromeService(driver_path)
    # configuring the driver
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    ver = int(driver.capabilities['chrome']['chromedriverVersion'].split('.')[0])
    driver.quit()
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.page_load_strategy = 'normal'
    chrome_options.add_argument("--disable-notifications")
    # disable location prompts & disable images loading
    prefs = {"profile.default_content_setting_values.geolocation": 2, "profile.managed_default_content_settings.images": 2, "profile.default_content_setting_values.cookies": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = uc.Chrome(version_main = ver, options=chrome_options) 
    driver.set_window_size(1920, 1080)
    driver.maximize_window()
    driver.set_page_load_timeout(300)

    return driver


def scrape_bookclubs(path):

    start = time.time()
    print('-'*75)
    print('Scraping bookclubs.com ...')
    print('-'*75)
    # initialize the web driver
    driver = initialize_bot()

    # initializing the dataframe
    data = pd.DataFrame()

    # if no books links provided then get the links
    if path == '':
        name = 'bookclubs_data.csv'   
        links = []
        # scraping books urls
        driver.get('https://bookclubs.com/discussion-guides')
        
        print('Getting the full list of books ...')
        # handling lazy loading
        while True:
            try:
                htmlelement= wait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "html")))
                htmlelement.send_keys(Keys.END)
                time.sleep(1)
                div = wait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class='content-discussion center']")))
                button = wait(div, 2).until(EC.presence_of_element_located((By.TAG_NAME, "button")))
                driver.execute_script("arguments[0].click();", button)
                time.sleep(4)
            except:
                break
    
        print('-'*75)
        nbooks = 0
        titles = wait(driver, 90).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[class='txt-link title']")))
        for title in titles:        
            try:
                links.append(title.get_attribute('href'))
                nbooks += 1
                print(f'Scraping url for book {nbooks}')
            except Exception as err:
                pass

        # saving the links to a csv file
        print('-'*75)
        print('Exporting links to a csv file ....')
        with open('bookclubs_links.csv', 'w', newline='\n', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Link'])
            for row in links:
                writer.writerow([row])

    scraped = []
    if path != '':
        df_links = pd.read_csv(path)
        name = path.split('\\')[-1][:-4]
    else:
        df_links = pd.read_csv('bookclubs_links.csv')
        name = 'bookclubs_links'

    links = df_links['Link'].values.tolist() 
    name = name + '_data.xlsx'
    try:
        data = pd.read_excel(name)
        scraped = data['Title Link'].values.tolist()
    except:
        pass
    # scraping books details
    print('-'*75)
    print('Scraping Books Info...')
    n = 0
    nbooks = len(links)
    for i, link in enumerate(links):
        try:      
            if link in scraped: 
                n += 1
                continue
            driver.get(link)
            time.sleep(2)
            details = {}
            print(f'Scraping the info for book {n+1}/{nbooks}')
            n += 1

            title = ''
            try:
                title = wait(driver, 2).until(EC.presence_of_element_located((By.TAG_NAME, "h1"))).get_attribute('textContent').strip()
            except:
                pass

            details['Title'] = title
            details['Title Link'] = link

            author, author_link = '', ''
            try:
                tags = wait(driver, 2).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[class='author-name']")))
                for tag in tags:
                    author += tag.get_attribute('textContent') + ', '
                    author_link += tag.get_attribute('href') + ', '

                author = author[:-2]
                author_link = author_link[:-2]
            except:
                pass

            details['Author'] = author
            details['Author Link'] = author_link

            # Number of reads
            nread = ''
            try:
                nread = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//p[@class='rating mb20']"))).get_attribute('textContent').split()[0].strip()
            except:
                pass          
                
            details['Number of Reads'] = nread                
            
            # Number of pages
            npages = ''
            try:
                npages = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//p[@class='pages']"))).get_attribute('textContent').split()[0].strip()
            except:
                pass          
                
            details['Number of Pages'] = npages             
            
            # rating
            rating = ''
            try:
                text = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//p[@class='rating']"))).get_attribute('textContent')
                if ':' in text:
                    rating = text.split(':')[-1].strip()
            except:
                pass          
                
            details['Rating'] = rating                
         
            # number of reviews and ratings
            nrevs, nratings = '', ''
            try:
                div = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//div[@class='wrapper-rating-review']")))
                nratings = wait(div, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "p[class='rating']"))).get_attribute('textContent').split()[0]
                nrevs = wait(div, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "p[class='label-review']"))).get_attribute('textContent').split()[0]
            except:
                pass          
                
            details['Number of Ratings'] = nratings                
            details['Number of Reviews'] = nrevs                

            # Amazon Link
            Amazon = ''
            try:
                text = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[aria-label='Buy it on Amazon']"))).get_attribute('href')
                if 'amazon.com' in text:
                    Amazon = text
            except:
                pass          
                
            details['Amazon Link'] = Amazon
            
            # appending the output to the datafame            
            data = data.append([details.copy()])
            # saving data to csv file each 100 links
            if np.mod(i+1, 100) == 0:
                print('Outputting scraped data to Excel sheet ...')
                data.to_excel(name, index=False)
        except:
            pass

    # optional output to Excel
    data.to_excel(name, index=False)
    elapsed = round((time.time() - start)/60, 2)
    print('-'*75)
    print(f'bookclubs.com scraping process completed successfully! Elapsed time {elapsed} mins')
    print('-'*75)
    driver.quit()

    return data

if __name__ == "__main__":
    
    path = ''
    if len(sys.argv) == 2:
        path = sys.argv[1]
    data = scrape_bookclubs(path)
