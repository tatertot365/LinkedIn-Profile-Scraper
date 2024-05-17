import pandas as pd
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from linkedin_scraper import Person
from creds import linkedin_username, linkedin_password, imported_profile_list
from webdriver_manager.chrome import ChromeDriverManager
import re


# this logs into linkedin
def login():
    opts = Options()

    # This sets up the driver and opens the browser
    # driver = webdriver.Chrome(options=opts, executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(options=opts)

    driver.get("https://www.linkedin.com/login")
    sleep(5)

    # username is submitted
    username = driver.find_element(By.ID, 'username')
    username.send_keys(linkedin_username)

    sleep(0.5)

    # Password is submitted
    password = driver.find_element(By.ID, 'password')
    password.send_keys(linkedin_password)

    sleep(0.5)

    sign_in_button = driver.find_element(By.XPATH,'//* [@type="submit"]')

    # Sign in button is clicked
    sign_in_button.click()

    sleep(10)

    return driver

# get page soup
def get_soup(driver):

    # get the page source and parse it with beautiful soup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    return soup

# get name
def get_name(soup):
    # get the name from the profile page finding the header with the name
    try:
        name = soup.find('h1', {'class': 'text-heading-xlarge'}).text

        name = name.replace('"', '')
        name = name.replace(',', '')
        name = name.strip()
        name = re.findall(r'[^\W\d_]+|\s|\.', name, re.UNICODE)
        name = ''.join(name)

        while ("CFA" in name) or ("MBA" in name) or ("CFP" in name) or ("CPA" in name):
            name = name[:-3]
            name = name.strip()

        if "JD" in name:
            name = name[:-2]
            name = name.strip()

        if "CAMS" in name:
            name = name[:-4]
            name = name.strip()

    except:
        name = None


    return name

# get current position
def get_current_position(soup):

    # get the current position from the profile page if a person object is not passed in using a linkedin scraper package
    try:
        experience_section = soup.select("div.display-flex.flex-wrap.align-items-center.full-height")
        if experience_section[0].find_next_sibling().find_next_sibling():
            if ("mo" in experience_section[0].find_next_sibling().find_next_sibling().find("span").text) or ("yr" in experience_section[0].find_next_sibling().find_next_sibling().find("span").text):
                current_position = experience_section[0].find("span").text
            else:
                current_position = experience_section[1].find("span").text
        else:
            current_position = experience_section[1].find("span").text

        current_position = current_position.replace('"', '')
        current_position = current_position.replace(',', '')
        current_position = current_position.strip()
        
    except:
        current_position = None

    return current_position

# get current company
def get_current_company(soup):

    try:
        experience_section = soup.select("div.display-flex.flex-wrap.align-items-center.full-height")
        if "mo" in experience_section[0].find_next_sibling().find("span").text or "yr" in experience_section[0].find_next_sibling().find("span").text:
            current_company = experience_section[0].find("span").text
        else:
            current_company = experience_section[0].find_next_sibling().find("span").text
            for i in range(len(current_company)):
                if current_company[i] == "·":
                    current_company = current_company[:i]
                    break
        
        current_company = current_company.replace('"', '')
        current_company = current_company.replace(',', '')
        current_company = current_company.strip()

    except:
        current_company = None


    return current_company

# get graduation year
def get_graduation_year(soup):
    try:
        education_div = soup.select("div.pvs-header__left-container--stack")
        for div in education_div:
            if div.div.h2.span.text == "Education":
                education_div = div
                break

        education_spans = education_div.parent.parent.find_next_sibling().find_all("span", {'class': 'visually-hidden'})

        for i in range(len(education_spans)):
            if education_spans[i].text[:24] == "Brigham Young University":
                graduation_year = education_spans[i + 2].text[-4:]
                break

        try:
            graduation_year = int(graduation_year)
        except:
            graduation_year = None
        
    except:
        graduation_year = None

    return graduation_year

# this gets profile information from the linkedin profile page using beautiful soup
def get_profile_data(soup):

    # get the profile data calling the functions above
    name = get_name(soup)
    current_position = get_current_position(soup)
    current_company = get_current_company(soup)
    graduation_year = get_graduation_year(soup)

    print(name, current_position, current_company, graduation_year)

    # return [current_picture, name, current_position, current_company, graduation_year]
    return [name, current_position, current_company, graduation_year]


if __name__ == "__main__":
    # login to linkedin
    driver = login()

    # list of profiles to scrape using the linkedin profile url
    profile_list = imported_profile_list
    profile_data_df = pd.DataFrame(columns=['name', 'current_position', 'current_company', 'graduation_year', 'profile_url'])

    # loop through each profile in the list
    for name in profile_list:
        driver.get("https://www.linkedin.com/in/" + name)
        sleep(5)

        profile_url = "https://www.linkedin.com/in/" + name

        # get the page source and parse it with beautiful soup
        soup = get_soup(driver)
        sleep(5)


        # get the profile data and add it to the dataframe
        profile_data = get_profile_data(soup)
        profile_data.append(profile_url)
        profile_data_df.loc[name] = profile_data

    def get_last_name(name):
        return name.split()[-1]
    

    profile_data_df['last_name'] = profile_data_df['name'].apply(get_last_name)
    profile_data_df.sort_values(by=['last_name'], inplace=True)
    profile_data_df.drop('last_name', axis=1, inplace=True)

    # save the data to a csv file
    profile_data_df.to_csv('profile_data.csv', index=False)

    # close the browser
    driver.quit()