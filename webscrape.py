import pandas as pd
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from linkedin_scraper import Person, actions
from creds import linkedin_username, linkedin_password, imported_profile_list

# this logs into linkedin
def login():
    opts = Options()

    # This sets up the driver and opens the browser
    driver = webdriver.Chrome(options=opts, executable_path= "chromedriver")

    driver.get("https://www.linkedin.com/")
    sleep(5)

    # username is submitedd
    username = driver.find_element(By.ID, 'session_key')
    username.send_keys(linkedin_username)

    sleep(0.5)

    # Password is submitted
    password = driver.find_element(By.ID, 'session_password')
    password.send_keys(linkedin_password)

    sleep(0.5)

    sign_in_button = driver.find_element(By.XPATH,'//* [@type="submit"]')

    # Sign in button is clicked
    sign_in_button.click()

    sleep(15)

    return driver

# get page soup
def get_soup(driver):

    # get the page source and parse it with beautiful soup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    return soup

# get current picture
"""def get_current_picture(soup):
    try:
        current_picture = soup.find('img', {'class': 'pv-top-card-profile-picture__image pv-top-card-profile-picture__image--show evi-image ember-view'})['src']
    except:
        current_picture = None

    return current_picture"""

# get name
def get_name(soup):

    try:
        name = soup.find('h1', {'class': 'text-heading-xlarge'}).text

        if name[-3:] in ['CFA', 'MBA']:
            name = name[:-3]
    except:
        name = None

    # clean up name
    name = name.replace('\n', '')
    name = name.replace('"', '')
    name = name.replace(',', '')
    name = name.strip()

    return name

# get current position
def get_current_position(person, soup, name):

    if person is None:
        try:
            experience_section = soup.find('div', {'id': 'experience'})
            jobs_div = experience_section.find_next('div', {'class': 'pvs-list__outer-container'}).findChildren()[0]
            jobs_list = jobs_div.findChildren()

            # loop through each list item and get the current position
            jobs_array = []
            for job in jobs_list:
                potential = job.find_next('span', {'class': 'visually-hidden'}).text

                if potential not in jobs_array:
                    jobs_array.append(potential)

                if 'Present' in potential:
                    ############################# This is where you need to add a name if it is not getting the position correctly #############################
                    if name in ["Corrine Richter", "Juan Jorge Poémape"]:
                        current_position = jobs_array[-2]
                    else:
                        current_position = jobs_array[-3]
                    break
        except:
            current_position = None

    else:
        try:
            current_position = person.experiences[0].position_title
        except:
            current_position = None

    # clean up current position
    current_position = current_position.replace('\n', '')
    current_position = current_position.replace('"', '')
    current_position = current_position.replace(',', '')
    current_position = current_position.strip()

    return current_position

# get current company
def get_current_company(person, soup):

    if person is None:
        try:
            current_company = soup.find('div', {'class': 'inline-show-more-text inline-show-more-text--is-collapsed inline-show-more-text--is-collapsed-with-line-clamp inline'}).text
            current_company = current_company.replace('\n', '')
            current_company = current_company.replace('"', '')
            current_company = current_company.replace(',', '')
            current_company = current_company.strip()
        except:
            current_company = None
    else:
        try:
            current_company = person.experiences[0].institution_name

            if current_company[-9:] in ["Full-time", "Part-time", "Freelance"]:
                current_company = current_company[:-12]
            elif current_company[-13:] == "Self-employed":
                current_company = current_company[:-16]
            elif current_company[-8:] in ["Contract", "Seasonal"]:
                current_company = current_company[:-11]
            elif current_company[-10:] == "Internship":
                current_company = current_company[:-13]
            elif current_company[-14:] == "Apprenticeship":
                current_company = current_company[:-17]

        except:
            current_company = None

    return current_company

# get graduation year
def get_graduation_year(soup):
    try:
        # navigate to the education section
        education_section = soup.find('div', {'id': "education"})
        education_section = education_section.find_parent('section', {'class': 'artdeco-card ember-view relative break-words pb3 mt2'})

        # get school list form the profile page and education section
        education_div = education_section.findChildren()[1]
        school_list = education_div.find_next('div', {'class': 'pvs-list__outer-container'}).findChildren()[0]
        school_list = school_list.findChildren()

        # loop through each list item and get the graduation year
        graduation_year = None
        for school in school_list:
            school_name = school.find_next('span', {'class': 'visually-hidden'}).text
            if school_name[:24] == "Brigham Young University":
                graduation_year = school.find_next('span', {'class': 'visually-hidden'}).find_next('span', {'class': 'visually-hidden'}).find_next('span', {'class': 'visually-hidden'}).text
                graduation_year = int(graduation_year[-4:])
                break

    except:
        graduation_year = None

    return graduation_year

# this gets profile information from the linkedin profile page using beautiful soup
def get_profile_data(soup, person):

    # get the profile data calling the functions above
    # current_picture = get_current_picture(soup)
    name = get_name(soup)
    current_position = get_current_position(person, soup, name)
    current_company = get_current_company(person, soup)
    graduation_year = get_graduation_year(soup)

    # return [current_picture, name, current_position, current_company, graduation_year]
    return [name, current_position, current_company, graduation_year]

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

    try:
        person = Person(profile_url, driver=driver, close_on_complete=False)
    except:
        person = None

    # get the profile data and add it to the dataframe
    profile_data = get_profile_data(soup, person)
    profile_data.append(profile_url)
    profile_data_df.loc[name] = profile_data

# sort the dataframe by name from a to z
profile_data_df.sort_values(by=['name'], inplace=True)

# save the data to a csv file
profile_data_df.to_csv('alumni_profiles.csv', index=False)

# close the browser
driver.quit()