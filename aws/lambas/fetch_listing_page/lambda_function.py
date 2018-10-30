import json
import requests
import re
import boto3
from bs4 import BeautifulSoup

MAIN_PAGE_BASE = 'https://themedalofhonor.com'

def get_regex_for_class_contains(class_):
  escaped_class = re.escape(class_)
  return re.compile('.*\ {}\ .*|.*\ {}$|^{}\ .*|^{}$'.format(escaped_class, escaped_class, escaped_class, escaped_class))

def extract_recipients(page_num):
  log_base = 'extract_recipients[{}] '.format(page_num)
  print log_base
  response = requests.get(MAIN_PAGE_BASE + '/medal-of-honor-recipients?sort-type=MostRecent&page-number=' + str(page_num))
  status_code = response.status_code
  if status_code != 200:
    print status_code
    return []

  print log_base + 'fetched page with 200'
  soup = BeautifulSoup(response.text, 'html.parser')
  print log_base + 'parsed page'
  links = soup.find_all('a', href=re.compile('^\/medal\-of\-honor\-recipients\/recipients\/.+'))
  print log_base + 'found links'
  abs_links = map(lambda link: MAIN_PAGE_BASE + link.get('href'), links)
  print log_base + 'transformed links'
  return abs_links

def lambda_handler(event, context):
  page = int(event['Records'][0]['Sns']['Message'])
  recipient_urls = extract_recipients(page)

  # publish the recipient pages to fetch on AWS SNS
  client = boto3.client('sns')
  for recipient_url in recipient_urls:
    msg = recipient_url
    print 'msg={}'.format(msg)
    response = client.publish(
      TopicArn='arn:aws:sns:us-east-1:867953006382:MedalOfHonorInfo_RecipentEvent',
      Message=msg
    )
    print 'response={}'.format(response)

  return {
    "statusCode": 200,
    "body": json.dumps('Hello from Lambda!')
  }
