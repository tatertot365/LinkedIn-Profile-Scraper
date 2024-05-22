import pandas as pd
import boto3
import re
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from creds import linkedin_username, linkedin_password, li_at_cookie, imported_profile_list, aws_s3_secret_access_key_id, aws_s3_access_key, aws_s3_bucket


# this logs into linkedin
def login() -> webdriver.Chrome:
    opts = Options()

    # This sets up the driver and opens the browser
    # driver = webdriver.Chrome(options=opts, executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(options=opts)

    if li_at_cookie:
        driver.delete_all_cookies()
        driver.get("https://www.linkedin.com")
        sleep(5)
        driver.add_cookie({'name': 'li_at', 'value': li_at_cookie, 'domain': '.linkedin.com'})
        sleep(2)
        driver.refresh()
        sleep(2)
        return driver

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

    sleep(5)

    return driver

# get page soup
def get_soup(driver: webdriver.Chrome) -> BeautifulSoup:

    # get the page source and parse it with beautiful soup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    return soup

# this gets profile information from the linkedin profile page using beautiful soup
def get_profile_data(soup: BeautifulSoup) -> list:

    # get the profile data calling the functions above
    name = get_name(soup)
    current_position = get_current_position(soup)
    current_company = get_current_company(soup)
    graduation_year = get_graduation_year(soup)

    print(name, current_position, current_company, graduation_year)

    return [name, current_position, current_company, graduation_year]

# get name
def get_name(soup: BeautifulSoup) -> str:
    # get the name from the profile page finding the header with the name
    try:
        name = soup.find('h1', {'class': 'text-heading-xlarge'}).text

        name = name.replace('"', '')
        name = name.replace(',', '')
        name = name.strip()
        name = re.findall(r'[^\W\d_]+|\s|\.', name, re.UNICODE)
        name = ''.join(name)

        abbreviations = ["CFA", "MBA", "CFP", "CPA", "JD", "CAMS"]

        for abbreviation in abbreviations:
            name = name.replace(abbreviation, '')
            name = name.strip()

    except Exception:
        name = None


    return name

# get current position
def get_current_position(soup: BeautifulSoup) -> str:

    try:
        experience_section = soup.select("div.display-flex.flex-wrap.align-items-center.full-height")
        # if studied, work, or group is in the first experience section, then the current position is in the second experience section
        i = 0
        while ("stud" in experience_section[i].find("span").text.lower()) or ("work" in experience_section[i].find("span").text.lower()) or ("group" in experience_section[i].find("span").text.lower()): 
            i += 1

        if experience_section[i].find_next_sibling().find_next_sibling() and "Top" not in experience_section[i].find("span").text:
            if ("mo" in experience_section[i].find_next_sibling().find_next_sibling().find("span").text) or ("yr" in experience_section[i].find_next_sibling().find_next_sibling().find("span").text):
                current_position = experience_section[i].find("span").text
            else:
                current_position = experience_section[i+1].find("span").text
        else:
            if "Top" in experience_section[i].find("span").text:
                if experience_section[i+1].find_next_sibling().find_next_sibling():
                    if ("mo" in experience_section[i+1].find_next_sibling().find_next_sibling().find("span").text) or ("yr" in experience_section[i+1].find_next_sibling().find_next_sibling().find("span").text):
                        current_position = experience_section[i+1].find("span").text
                    else:
                        current_position = experience_section[i+2].find("span").text
                else:
                    current_position = experience_section[i+2].find("span").text

            else:
                current_position = experience_section[i+1].find("span").text

        current_position = current_position.replace('"', '')
        current_position = current_position.replace(',', '')
        current_position = current_position.strip()

    except Exception:
        current_position = None

    return current_position

# get current company
def get_current_company(soup: BeautifulSoup) -> str:

    def extract_current_company(text):
        for i in range(len(text)):
            if text[i] == "·":
                text = text[:i]
                break
        return text

    try:
        experience_section = soup.select("div.display-flex.flex-wrap.align-items-center.full-height")

        i = 0
        while ("stud" in experience_section[i].find("span").text.lower()) or ("work" in experience_section[i].find("span").text.lower()) or ("group" in experience_section[i].find("span").text.lower()): 
            i += 1

        if ("mo" in experience_section[i].find_next_sibling().find("span").text) or ("yr" in experience_section[i].find_next_sibling().find("span").text) and ("Top" not in experience_section[i].find("span").text):
            current_company = experience_section[i].find("span").text
        else:
            if "Top" in experience_section[i].find("span").text:
                if ("mo" in experience_section[i+1].find_next_sibling().find("span").text) or ("yr" in experience_section[i+1].find_next_sibling().find("span").text):
                    current_company = experience_section[i+1].find("span").text
                else:
                    current_company = extract_current_company(experience_section[i+1].find_next_sibling().find("span").text)
            else:
                current_company = extract_current_company(experience_section[i].find_next_sibling().find("span").text)
        
        current_company = current_company.replace('"', '')
        current_company = current_company.replace(',', '')
        current_company = current_company.strip()

    except Exception:
        current_company = None

    return current_company

# get graduation year
def get_graduation_year(soup: BeautifulSoup) -> int:
    try:
        education_divs = soup.select("div.pvs-header__left-container--stack")
        for div in education_divs:
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
        except ValueError:
            graduation_year = None
        
    except Exception:
        graduation_year = None

    return graduation_year

def add_data_to_dataframe(profile_list: list, driver: webdriver.Chrome) -> pd.DataFrame:
    # profile_data_df = pd.DataFrame(columns=['name', 'current_position', 'current_company', 'graduation_year', 'profile_url'])
    profile_data_df = pd.read_csv('profile_data.csv')
    for name in profile_list:
        driver.get("https://www.linkedin.com/in/" + name)
        sleep(8)

        profile_url = "https://www.linkedin.com/in/" + name

        # get the page source and parse it with beautiful soup
        soup = get_soup(driver)
        sleep(5)


        # get the profile data and add it to the dataframe
        profile_data = get_profile_data(soup)
        profile_data.append(profile_url)
        profile_data_df.loc[name] = profile_data

    return profile_data_df

def sort_df_by_last_name(profile_data_df: pd.DataFrame) -> pd.DataFrame:
    def get_last_name(name):
        return name.split()[-1]
    

    profile_data_df['last_name'] = profile_data_df['name'].apply(get_last_name)
    profile_data_df.sort_values(by=['last_name'], inplace=True)
    profile_data_df.drop('last_name', axis=1, inplace=True)

    return profile_data_df

def upload_profile_data_to_AWS_S3() -> None:
    s3 = boto3.client('s3', aws_access_key_id=aws_s3_secret_access_key_id, aws_secret_access_key=aws_s3_access_key)

    s3.upload_file('profile_data.csv', aws_s3_bucket, 'profile_data.csv')

if __name__ == "__main__":
    # login to linkedin
    driver = login()

    # list of profiles to scrape using the linkedin profile url
    profile_data_df = add_data_to_dataframe(imported_profile_list, driver)

    # sort the data by last name
    profile_data_df_sorted = sort_df_by_last_name(profile_data_df)

    # save the data to a csv file
    profile_data_df_sorted.to_csv('profile_data.csv', index=False)

    # close the browser
    driver.quit()

    # upload the data to AWS S3
    upload_profile_data_to_AWS_S3()