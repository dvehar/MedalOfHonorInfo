import json
import requests
import re
import boto3
from bs4 import BeautifulSoup

MAIN_PAGE_BASE = 'https://themedalofhonor.com'

def get_regex_for_class_contains(class_):
  escaped_class = re.escape(class_)
  return re.compile('.*\ {}\ .*|.*\ {}$|^{}\ .*|^{}$'.format(escaped_class, escaped_class, escaped_class, escaped_class))

def extract_recipient_info(url):
  log_base = 'extract_recipient_info[{}] '.format(url)
  print log_base

  response = requests.get(url)
  status_code = response.status_code
  if status_code != 200:
    print status_code
    return {}

  print log_base + 'fetched page with 200'
  soup = BeautifulSoup(response.text, 'html.parser')
  print log_base + 'parsed page'

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

def dict_to_dynamodb_dict(raw_dict):
  formatted_dict = {}
  for key in raw_dict.keys():
    val = raw_dict[key]
    type = 'N' if isinstance(val, (int, long)) else 'S'
    formatted_dict[key] = { type: val }
  return formatted_dict

def lambda_handler(event, context):
  recipient_url = event['Records'][0]['Sns']['Message']
  recipient_data = extract_recipient_info(recipient_url)

  # insert the data into dynamodb
  print 'writing the data to dynamodb'
  client = boto3.client('dynamodb')
  response = client.put_item(TableName='MedalOfHonorInfo', Item=dict_to_dynamodb_dict(recipient_data))
  print 'response={}'.format(response)

  return {
    "statusCode": 200,
    "body": json.dumps('Hello from Lambda!')
  }
