from bs4 import BeautifulSoup
import requests
import time
from datetime import datetime, timezone
import os

# Set working directory
getdir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))  # http://stackoverflow.com/questions/918154/relative-paths-in-python
os.chdir(getdir)
if os.path.isfile('Wuhan_nCoV_Github_Project_list.csv'):
    os.rename('Wuhan_nCoV_Github_Project_list.csv', 'Wuhan_nCoV_Github_Project_list.old.csv')

with open('Wuhan_nCoV_Github_Project_list.csv', 'w') as file:
    file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format( \
            'Description', 'Address', 'Last Update', 'Language', 'License', 'Star', 'Topics', 'Issues Need Help'))

NO_OLDER_PROJECT = False


for i in range(1, 20):
    print(i) ##test
    if i%8 == 0:
        time.sleep(60) # Github may only allow scrap about 10 page at a time...
    if NO_OLDER_PROJECT == True:
        break
    response = requests.get("https://github.com/search?o=desc&p={}&q=武汉&s=updated&type=Repositories".format(i))
    doc = response.text
    soup = BeautifulSoup(doc, 'html.parser')

    list_raw = soup.find('ul', class_='repo-list').find_all('li')

    result = []

    for item in list_raw:
        date = item.find('relative-time').get('datetime')
        date = datetime.fromisoformat(date[0:-1])
        # the oldest project related to wuhan 2019-nCoV is after 2020-01-20
        if date < datetime(2020, 1, 20):
            NO_OLDER_PROJECT = True
            break
        # convert date to local timezone and format it to easy-reading string
        date = date.replace(tzinfo=timezone.utc).astimezone(tz=None).strftime('%Y-%m-%d %H:%M:%S %Z%z')
        description = item.find('p').text.strip()
        link_list = item.find_all('a')
        url_raw = link_list[0]
        url = [url for url in str(url_raw).split('"') if 'http' in url][0]
        description_list = item.find(class_='text-small').find_all('div')

        # real-time star count can be extracted from project_url/stargazers
        try:
            language = item.find(attrs={'itemprop': 'programmingLanguage'}).text
        except Exception as error:
            language = 'None'

        star_count = description_list[0].text.strip()
        if star_count[0] not in '0123456789':
            star_count = 0

        if len(description_list) > 1 and description_list[-2].text.strip() not in [language, star_count]:
            license = description_list[-2].text.strip()
        else:
            license = 'None'

        issues_need_help_raw = link_list[-1].text.strip()
        if issues_need_help_raw[-4:] == 'help':
            issues_need_help = issues_need_help_raw[0]
        else:
            issues_need_help_raw = ''
            issues_need_help = 0

        try:
            topic_list = []
            for topic in link_list[1:]:
                if topic.text.strip() not in [star_count, issues_need_help_raw]:
                    topic_list.append(topic.text.strip())
            topic_list = ', '.join(topic_list)
        except Exception as error:
            pass
        if topic_list == [] or topic_list == '':
            topic_list = 'None'

        result.append('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}'.format( \
                description, url, date, language, license, star_count, topic_list, issues_need_help))

    with open('Wuhan_nCoV_Github_Project_list.csv', 'a') as file:
        for i in result:
            file.write('{}\n'.format(i))
