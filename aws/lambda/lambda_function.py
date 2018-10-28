import json
import requests
import re
import multiprocessing
from bs4 import BeautifulSoup
from joblib import Parallel, delayed

MAIN_PAGE_BASE = 'https://themedalofhonor.com'
num_cores = multiprocessing.cpu_count()

def get_regex_for_class_contains(class_):
  escaped_class = re.escape(class_)
  return '.*\ {}\ .*|.*\ {}$|^{}\ .*|^{}$'.format(escaped_class, escaped_class, escaped_class, escaped_class)

def extract_page_count():
  response = requests.get(MAIN_PAGE_BASE + '/medal-of-honor-recipients?sort-type=MostRecent&page-number=1')
  status_code = response.status_code
  if status_code != 200:
    print status_code
    return 0

  soup = BeautifulSoup(response.text, 'html.parser')
  page_selectors = soup.find('div', class_=re.compile(get_regex_for_class_contains('recipient-grid'))).find_all('a', class_=re.compile(get_regex_for_class_contains('page-selector')))
  return int(page_selectors[-1].get('data-pagenumber'))

def extract_recipients(page_num):
  response = requests.get(MAIN_PAGE_BASE + '/medal-of-honor-recipients?sort-type=MostRecent&page-number=' + str(page_num))
  status_code = response.status_code
  if status_code != 200:
    print status_code
    return []

  soup = BeautifulSoup(response.text, 'html.parser')
  links = soup.find_all('a', href=re.compile('^\/medal\-of\-honor\-recipients\/recipients\/.+'))
  abs_links = map(lambda link: MAIN_PAGE_BASE + link.get('href'), links)
  return abs_links

def _extract_recipient_info(url):
  print url
  response = requests.get(url)
  status_code = response.status_code
  if status_code != 200:
    print status_code
    return {}

  soup = BeautifulSoup(response.text, 'html.parser')

  name = soup.find('body').find('div', class_=re.compile('.*\ title\ .*|.*\ title$|^title\ .*|^title$')).find('h4').string
  name_match = re.compile('(.+)\,\ (.+)').match(name)
  if name_match == None:
    formatted_name = name
  else:
    formatted_name = name_match.group(2) + ' ' + name_match.group(1)

  citation = soup.find('div', id='citation').find('p').string

  year_of_honor = soup.find_all('table')[1].find_all('tr')[1].find_all('td')[1].string

  data = {
    'name': formatted_name,
    'citation': citation,
    'year_of_honor': year_of_honor
  }
  return data

def extract_recipient_info(urls):
  return map(_extract_recipient_info, urls)

def lambda_handler(event, context):
  page_count = extract_page_count()
  recipient_links = Parallel(n_jobs=num_cores)(delayed(extract_recipients)(i) for i in range(1, page_count + 1))
  recipient_info = []
  # recipient_info.extend(Parallel(n_jobs=num_cores)(delayed(extract_recipient_info)(recipient_links[i]) for i in range(1, page_count + 1)))
  for urls in recipient_links:
    recipient_info.extend(extract_recipient_info(urls))
  print recipient_info[-1]

  return {
    "statusCode": 200,
    "body": json.dumps('Hello from Lambda!')
  }
