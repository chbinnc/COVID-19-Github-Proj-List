from bs4 import BeautifulSoup
import requests
import time
from datetime import datetime, timezone
import os, inspect

def isInBlacklist(description):
    for keyword in keyword_blacklist:
        if keyword in description:
            #print("{} is not a related project.".format(description)) ##test
            return True
    return False

def main(search_keywords, saved_project_list, saved_address_list, NEW=False):
    OLDEST_DATE = datetime(2020, 1, 20).replace(tzinfo=timezone.utc)
    for search_keyword in search_keywords:
        NO_OLDER_PROJECT = False
        print('Searching with keyword: {}'.format(search_keyword))
        for page in range(1, 200):
            if page % 8 == 0:
                print('Wait one minute as Github only allow scrap about 10 pages at a time.')
                time.sleep(60)
            if NO_OLDER_PROJECT == True:
                break
            print('Page: {}, saved projects: {}'.format(page, len(saved_project_list))) ##test
            response = requests.get("https://github.com/search?o=desc&p={}&q={}&s=updated&type=Repositories".\
                    format(page, search_keyword))
            doc = response.text
            soup = BeautifulSoup(doc, 'html.parser')

            list_raw = soup.find('ul', class_='repo-list').find_all('li')

            for item in list_raw:
                date = item.find('relative-time').get('datetime')
                date = datetime.fromisoformat(date[0:-1]).replace(tzinfo=timezone.utc)
                # for old keywords, only scrap new and updated project.
                if NEW == False:
                    if date < last_updated_date:
                        print("No older project before {}, done!".format(last_updated_date_raw))
                        NO_OLDER_PROJECT = True
                        break
                # the oldest project related to wuhan 2019-nCoV is after 2020-01-20
                if date < OLDEST_DATE:
                    print("No older project before 2020-01-20, done!")
                    NO_OLDER_PROJECT = True
                    break
                # convert date to local timezone and format it to easy-reading string
                date = date.astimezone(tz=None).strftime('%Y-%m-%d %H:%M:%S %Z%z')

                link_list = item.find_all('a')
                url_raw = link_list[0]
                url = [url for url in str(url_raw).split('"') if 'http' in url][0]

                try:
                    description = item.find('p').text.strip()
                except Exception as error:
                    # use project name as description instead
                    description = url.split('/')[-1]
                if isInBlacklist(description) == True:
                    continue

                extra_info_list = item.find(class_='text-small').find_all('div')

                try:
                    language = item.find(attrs={'itemprop': 'programmingLanguage'}).text
                except Exception as error:
                    language = 'None'

                star_count = extra_info_list[0].text.strip()
                if star_count[0] not in '0123456789':
                    star_count = 0

                if len(extra_info_list) > 1 and \
                        extra_info_list[-2].text.strip() not in [language, star_count]:
                    license = extra_info_list[-2].text.strip()
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
                        topic_text_strip = topic.text.strip()
                        if topic_text_strip not in [star_count, issues_need_help_raw] and \
                                topic_text_strip[0:4] != 'http':
                            topic_list.append(topic_text_strip)
                    topic_list = ', '.join(topic_list)
                except Exception as error:
                    pass
                if topic_list == [] or topic_list == '':
                    topic_list = 'None'

                if url in saved_address_list:
                    #print("{} is already saved.".format(url)) ##test
                    for row in saved_project_list:
                        if url in row:
                            saved_project_list[saved_project_list.index(row)] = \
                                    [description, url, date, language, \
                                    license, star_count, topic_list, issues_need_help]
                            break
                else:
                    saved_address_list.append(url)
                    saved_project_list.append([description, url, date, language, \
                            license, star_count, topic_list, issues_need_help])
        # wait one minute except after searching the last keyword
        if search_keywords.index(search_keyword) != len(search_keywords) - 1:
            print('Wait one minute as Github only allow scrap about 10 pages at a time.')
            time.sleep(60)

    return saved_project_list, saved_address_list

if __name__ == '__main__':
    # Set working directory
    getdir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))  # http://stackoverflow.com/questions/918154/relative-paths-in-python
    os.chdir(getdir)
    with open('search_keywords.old.txt') as file:
        old_search_keywords = file.read().split('\n')
        old_search_keywords = list(filter(lambda a: a != '', old_search_keywords))
    with open('search_keywords.txt') as file:
        search_keywords = file.read().split('\n')
        search_keywords = list(filter(lambda a: a != '', search_keywords))
    with open('keyword_blacklist.txt') as file:
        keyword_blacklist = file.read().split('\n')
        keyword_blacklist = list(filter(lambda a: a != '', keyword_blacklist))
        print('Keyword blacklist: {}'.format(keyword_blacklist))
    with open('last_updated_date.txt') as file:
        last_updated_date_raw = file.read().strip()
        last_updated_date = datetime.strptime(last_updated_date_raw, '%Y-%m-%d %H:%M:%S %Z%z')

    saved_project_list = []
    saved_address_list = []
    with open('Wuhan_nCoV_Github_Project_list.csv') as file:
        IS_HEADER = True
        for row in file:
            if IS_HEADER:
                IS_HEADER = False
                continue
            row_split = row.strip().split('\t')
            if not isInBlacklist(row_split[0]):
                saved_project_list.append(row_split)
                saved_address_list.append(row_split[1]) # use address for checking duplicate project
    # search with keyword in search_keywords.txt
    saved_project_list, saved_address_list = main(\
            search_keywords, saved_project_list, saved_address_list, NEW=True)

    if search_keywords != []:
        print('Wait one minute as Github only allow scrap about 10 pages at a time.')
        time.sleep(60)
    # search with keyword in search_keywords.old.txt
    saved_project_list, saved_address_list = main(\
            old_search_keywords, saved_project_list, saved_address_list)

    saved_project_list = sorted(saved_project_list, key=lambda entry: entry[2])[::-1] # sorted by date

    if os.path.isfile('Wuhan_nCoV_Github_Project_list.csv'):
        os.rename('Wuhan_nCoV_Github_Project_list.csv', 'Wuhan_nCoV_Github_Project_list.old.csv')
    with open('Wuhan_nCoV_Github_Project_list.csv', 'w') as file:
        file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format( \
                'Description', 'Address', 'Last Update', 'Language', \
                'License', 'Star', 'Topics', 'Issues Need Help'))

    with open('Wuhan_nCoV_Github_Project_list.csv', 'a') as file:
        for i in saved_project_list:
            file.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format( \
                        i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7]))

    last_updated_date = saved_project_list[0][2]
    with open('last_updated_date.txt', 'w') as file:
        file.write(last_updated_date)

    old_search_keywords += search_keywords
    # Move search keywords to search_keywords.old.txt
    with open('search_keywords.old.txt', 'w') as file:
        for i in old_search_keywords:
            file.write('{}\n'.format(i))
    with open('search_keywords.txt', 'w') as file:
        file.write('')
