import json
import requests
import re
import boto3
from bs4 import BeautifulSoup

MAIN_PAGE_BASE = 'https://themedalofhonor.com'

def get_regex_for_class_contains(class_):
  escaped_class = re.escape(class_)
  return re.compile('.*\ {}\ .*|.*\ {}$|^{}\ .*|^{}$'.format(escaped_class, escaped_class, escaped_class, escaped_class))

def extract_page_count():
  url = MAIN_PAGE_BASE + '/medal-of-honor-recipients?sort-type=MostRecent&page-number=1'
  print 'scraping ' + url
  response = requests.get(url)
  status_code = response.status_code
  if status_code != 200:
    print status_code
    return 0

  soup = BeautifulSoup(response.text, 'html.parser')
  page_selectors = soup.find('div', class_=re.compile(get_regex_for_class_contains('recipient-grid'))).find_all('a', class_=get_regex_for_class_contains('page-selector'))
  return int(page_selectors[-1].get('data-pagenumber'))

def lambda_handler(event, context):
  # get number of pages
  page_count = extract_page_count()
  print 'found ' + str(page_count) + ' pages'

  # publish the pages to fetch on AWS SNS
  client = boto3.client('sns')
  for i in range(1, page_count + 1):
    msg = str(i)
    print 'msg={}'.format(msg)
    response = client.publish(
      TopicArn='arn:aws:sns:us-east-1:867953006382:MedalOfHonorInfo_PageEvent',
      Message=msg
    )
    print 'response={}'.format(response)

  return {
    "statusCode": 200,
    "body": json.dumps('Hello from Lambda!')
  }
