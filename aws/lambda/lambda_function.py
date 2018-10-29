import json
import requests
import re
import multiprocessing
from threading import Thread
from queue import Queue
import sys
import boto3
from bs4 import BeautifulSoup
from joblib import Parallel, delayed

MAIN_PAGE_BASE = 'https://themedalofhonor.com'
num_cores = multiprocessing.cpu_count()

def get_regex_for_class_contains(class_):
  escaped_class = re.escape(class_)
  return re.compile('.*\ {}\ .*|.*\ {}$|^{}\ .*|^{}$'.format(escaped_class, escaped_class, escaped_class, escaped_class))

def extract_page_count():
  response = requests.get(MAIN_PAGE_BASE + '/medal-of-honor-recipients?sort-type=MostRecent&page-number=1')
  status_code = response.status_code
  if status_code != 200:
    print status_code
    return 0

  soup = BeautifulSoup(response.text, 'html.parser')
  page_selectors = soup.find('div', class_=re.compile(get_regex_for_class_contains('recipient-grid'))).find_all('a', class_=get_regex_for_class_contains('page-selector'))
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

  name = soup.find('body').find('div', class_=get_regex_for_class_contains('title')).find('h4').string
  name_match = re.compile('(.+)\,\ (.+)').match(name)
  if name_match == None:
    formatted_name = name
  else:
    formatted_name = name_match.group(2) + ' ' + name_match.group(1)

  citation = soup.find('div', id='citation').find('p').string

  year_of_honor = soup.find_all('table')[1].find_all('tr')[1].find_all('td')[1].string

  img = soup.find('div', id='the-top').find('div', class_=get_regex_for_class_contains('callout-img')).find('img')
  img = MAIN_PAGE_BASE + img.get('src')

  data = {
    'name': formatted_name,
    'citation': citation,
    'year_of_honor': year_of_honor,
    'img': img
  }
  return data

def extract_recipient_info(urls, i):
  return _extract_recipient_info(urls[i])

def dict_to_dynamodb_dict(raw_dict):
  formatted_dict = {}
  for key in raw_dict.keys():
    val = raw_dict[key]
    type = 'N' if isinstance(val, (int, long)) else 'S'
    formatted_dict[key] = { type: val }
  return formatted_dict

class Worker(Thread):
  def __init__(self, queue, results, fn):
    Thread.__init__(self)
    self.queue = queue
    self.results = results
    self.fn = fn

  def run(self):
    while True:
      # Get the work from the queue and expand the tuple
      arg = self.queue.get()
      try:
        self.results.put(self.fn(arg))
      finally:
        self.queue.task_done()

def lambda_handler(event, context):
  page_count = extract_page_count()
  # recipient_links = Parallel(n_jobs=num_cores)(delayed(extract_recipients)(i) for i in range(1, page_count + 1))
  recipient_links = Parallel(n_jobs=num_cores)(delayed(extract_recipients)(i) for i in range(1, 4))
  # recipient_info = []
  # for urls in recipient_links:
  #   recipient_info.extend(extract_recipient_info(urls))
  # print recipient_info[-1]
  #
  # r = [item for sublist in recipient_links for item in sublist]
  # recipient_info = Parallel(n_jobs=2, verbose=100)(delayed(extract_recipient_info)(r, i) for i in range(1,4))

  results = Queue()
  # Create a queue to communicate with the worker threads
  queue = Queue()
  for _ in range(num_cores):
    worker = Worker(queue, results, _extract_recipient_info)
    # Setting daemon to True will let the main thread exit even though the workers are blocking
    worker.daemon = True
    worker.start()
  for recipient_link in [item for sublist in recipient_links for item in sublist]:
    queue.put(recipient_link)
  queue.join()
  while not results.empty():
    r = results.get()
    if (results.empty()):
      print r

  # client = boto3.client('dynamodb')
  # response = client.put_item(TableName='MedalOfHonorInfo', Item=dict_to_dynamodb_dict(recipient_info[-1]))

  # todo: persist recipient_info in DB
  # todo: add alexa request processing stuff
  #       - What is the Medal of Honor?
  #         - The Medal of Honor is the United States of America's highest and most prestigious personal military decoration that may be awarded to recognize U.S. military service members who have distinguished themselves by acts of valor. The medal is normally awarded by the President of the United States in the name of the U.S. Congress.
  #       - Who is the latest recipient?
  #         - Who is the latest recipient of the Medal of Honor?
  #       - Have any women been awarded the Medal of Honor?
  #         - Have any women ever been awarded the Medal of Honor?
  #         - Have any women been awarded?
  #         - Have any women ever been awarded?

  return {
    "statusCode": 200,
    "body": json.dumps('Hello from Lambda!')
  }
