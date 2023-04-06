import pandas as pd
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from creds import username, password, imported_profile_list

# this logs into linkedin
def login():
    opts = Options()

    driver = webdriver.Chrome(options=opts, executable_path= "chromedriver")

    driver.get("https://www.linkedin.com")

    username = driver.find_element(By.ID, 'session_key')
    username.send_keys(username)

    sleep(0.5)

    password = driver.find_element(By.ID, 'session_password')
    password.send_keys(password)

    sleep(0.5)

    sign_in_button = driver.find_element(By.XPATH,'//* [@type="submit"]')

    sign_in_button.click()

    sleep(10)

    return driver

# get page soup
def get_soup(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return soup

# this gets profile information from the linkedin profile page using beautiful soup
def get_profile_data(soup):

    # get name
    try:
        name = soup.find('h1', {'class': 'text-heading-xlarge'}).text
    except:
        name = 'No results'

    # get current position
    try:
        current_position = soup.find('div', {'class': 'text-body-medium break-words'}).text
    except:
        current_position = 'No results'

    # clean up current position
    current_position = current_position.replace('\n', '')
    current_position = current_position.replace('"', '')
    current_position = current_position.strip()

    # get current picture
    try:
        current_picture = soup.find('img', {'class': 'pv-top-card-profile-picture__image pv-top-card-profile-picture__image--show ember-view'})['src']
    except:
        current_picture = 'No results'

    return [name, current_position, current_picture]

# login to linkedin
driver = login()

# list of profiles to scrape using the linkedin profile url
profile_list = imported_profile_list
profile_data_df = pd.DataFrame(columns=['name', 'current_position', 'current_picture'])

# loop through each profile in the list
for name in profile_list:
    driver.get("https://www.linkedin.com/in/" + name)
    sleep(5)

    soup = get_soup(driver)
    profile_data = get_profile_data(soup)
    profile_data_df.loc[name] = profile_data

# save the data to a csv file
profile_data_df.to_csv('profile_data.csv', index=False)

# close the browser
driver.quit()