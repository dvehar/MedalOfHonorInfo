import logging
from datetime import datetime
import random
import string

import boto3
from boto3.dynamodb.conditions import Key

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard
from ask_sdk_model.ui import StandardCard
from ask_sdk_model.ui import Image
from ask_sdk_model import Response

sb = SkillBuilder()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LaunchRequestHandler(AbstractRequestHandler):
  """Handler for Skill Launch."""
  def can_handle(self, handler_input):
    # type: (HandlerInput) -> bool
    return is_request_type("LaunchRequest")(handler_input)

  def handle(self, handler_input):
    # type: (HandlerInput) -> Response
    speech_text = 'This skill can give you more information about the Medal of Honor and its recipients. Try saying "Alexa, ask Medal of Honor Info what is the Medal of Honor?"'

    session_attributes = handler_input.attributes_manager.session_attributes
    session_attributes['last_request'] = {
      'speech_text': speech_text
    }

    handler_input.response_builder\
      .speak(speech_text)\
      .set_card(
        SimpleCard("Medal of Honor Info", speech_text))\
          .set_should_end_session(False)
    return handler_input.response_builder.response

class RepeatIntentHandler(AbstractRequestHandler):
  """Handler for Repeat Intent"""
  def can_handle(self, handler_input):
    # type: (HandlerInput) -> bool
    return is_intent_name("AMAZON.RepeatIntent")(handler_input)

  def handle(self, handler_input):
    # type: (HandlerInput) -> Response
    session_attributes = handler_input.attributes_manager.session_attributes
    logger.info("session_attributes={}".format(session_attributes))

    if 'last_request' in session_attributes:
      last_request = session_attributes['last_request']

      handler_input.response_builder\
        .set_should_end_session(False)

      if 'citation' in last_request:
        handler_input.response_builder\
          .speak(last_request['citation'])
      elif 'speech_text' in last_request:
        handler_input.response_builder\
          .speak(last_request['speech_text'])
      else:
        logger.error('unhandled last_request in RepeatIntentHandler: {}'.format(last_request))
        speech_text = 'I\'m not sure what you want me to repeat. Try saying "Alexa, ask Medal of Honor Info what is the Medal of Honor?"'
        handler_input.response_builder\
          .speak(speech_text)\
          .set_card(
            SimpleCard("Medal of Honor Info", speech_text))\
          .set_should_end_session(True)
    else:
      speech_text = 'I\'m not sure what you want me to repeat. Try saying "Alexa, ask Medal of Honor Info what is the Medal of Honor?"'
      handler_input.response_builder\
        .speak(speech_text)\
        .set_card(
          SimpleCard("Medal of Honor Info", speech_text))\
        .set_should_end_session(True)

    return handler_input.response_builder.response

class LatestRecipientIntentHandler(AbstractRequestHandler):
  """Handler for Latest Recipient Intent"""
  def can_handle(self, handler_input):
    # type: (HandlerInput) -> bool
    return is_intent_name("LatestRecipient")(handler_input)

  def handle(self, handler_input):
    # type: (HandlerInput) -> Response

    # fetch data into dynamodb
    logger.info('searching for latest recipient in dynamodb')
    table = boto3.resource('dynamodb').Table('MedalOfHonorInfo')
    min_year = str(datetime.now().year - 5) # assume that the award will be given out at least every 5 years
    response = table.scan(FilterExpression=Key('year_of_honor').gt(min_year))
    print 'response={}'.format(response)

    # find recorded with greatest year_of_honor. there isn't much we can do about tie-breaking
    newest = max(response['Items'], key=lambda val: val['year_of_honor'])
    print 'newest={}'.format(newest)

    citation = response['Items'][0]['citation']
    year_of_honor = response['Items'][0]['year_of_honor']
    img = response['Items'][0]['img']
    name = response['Items'][0]['name']
    speech_text = citation
    handler_input.response_builder\
      .speak('{} was awarded the Medal of Honor in {}<break time="600ms"/>{}'.format(name, year_of_honor, speech_text))\
      .set_card(
        StandardCard(name, speech_text, Image(img, img)))\
      .set_should_end_session(False)

    session_attributes = handler_input.attributes_manager.session_attributes
    session_attributes['last_request'] = {
      'name': name,
      'citation': citation,
      'img': img
    }

    return handler_input.response_builder.response

class WomenAwardedIntentHandler(AbstractRequestHandler):
  """Handler for Women Awarded Intent"""
  def can_handle(self, handler_input):
    # type: (HandlerInput) -> bool
    return is_intent_name("WomenAwarded")(handler_input)

  def handle(self, handler_input):
    # type: (HandlerInput) -> Response

    women = ['Mary Walker']
    recipient = random.choice(women)

    # fetch data into dynamodb
    logger.info('searching for the woman {}'.format(recipient))
    table = boto3.resource('dynamodb').Table('MedalOfHonorInfo')
    response = table.query(KeyConditionExpression=Key('name').eq(recipient), Limit=1)
    print 'response={}'.format(response)

    citation = response['Items'][0]['citation']
    year_of_honor = response['Items'][0]['year_of_honor']
    img = response['Items'][0]['img']
    name = response['Items'][0]['name']
    speech_text = citation
    handler_input.response_builder\
      .speak('{} was awarded the Medal of Honor in {}<break time="600ms"/>{}'.format(name, year_of_honor, speech_text))\
      .set_card(
        StandardCard(name, speech_text, Image(img, img)))\
      .set_should_end_session(False)

    session_attributes = handler_input.attributes_manager.session_attributes
    session_attributes['last_request'] = {
      'name': name,
      'citation': citation,
      'img': img
    }

    return handler_input.response_builder.response

class WhatIsItIntentHandler(AbstractRequestHandler):
  """Handler for What Is It Intent"""
  def can_handle(self, handler_input):
    # type: (HandlerInput) -> bool
    return is_intent_name("WhatIsIt")(handler_input)

  def handle(self, handler_input):
    # type: (HandlerInput) -> Response
    speech_text = 'The Medal of Honor is the United States of America\'s highest and most prestigious personal '\
                  'military decoration that may be awarded to recognize U.S. military service members who have '\
                  'distinguished themselves by acts of valor. The medal is normally awarded by the President of the '\
                  'United States in the name of the U.S. Congress. Try saying "Alexa, ask Medal of Honor Info who is '\
                  'the latest recipient?"'
    img = 'https://s3.amazonaws.com/medalofhonorinfo/moh{}.jpg'.format(random.choice(range(1, 11)))
    handler_input.response_builder\
      .speak(speech_text)\
      .set_card(
        StandardCard('Medal of Honor Info', speech_text, Image(img, img)))\
      .set_should_end_session(False)

    session_attributes = handler_input.attributes_manager.session_attributes
    session_attributes['last_request'] = {
      'speech_text': speech_text,
      'img': img
    }

    return handler_input.response_builder.response

class RecipientIntentHandler(AbstractRequestHandler):
  """Handler for Recipient Intent"""
  def can_handle(self, handler_input):
    # type: (HandlerInput) -> bool
    return is_intent_name("RecipientIntent")(handler_input)

  def handle(self, handler_input):
    # type: (HandlerInput) -> Response

    slots = handler_input.request_envelope.request.intent.slots
    try:
      recipient = slots['recipient'].resolutions.resolutions_per_authority[0].values[0].value.name.title()
    except:
      recipient = slots['recipient'].value.title()

    # fetch data into dynamodb
    print 'searching for {} in dynamodb'.format(recipient)
    table = boto3.resource('dynamodb').Table('MedalOfHonorInfo')
    response = table.query(KeyConditionExpression=Key('name').eq(recipient), Limit=1)
    print 'response={}'.format(response)

    if len(response['Items']) == 0:
      speech_text = 'There are no Medal of Honor recipients by the name of {}'.format(recipient)
      handler_input.response_builder.speak(speech_text)

      session_attributes = handler_input.attributes_manager.session_attributes
      session_attributes['last_request'] = {
        'speech_text': speech_text
      }
    else:
      citation = response['Items'][0]['citation']
      year_of_honor = response['Items'][0]['year_of_honor']
      img = response['Items'][0]['img']
      name = response['Items'][0]['name']
      speech_text = citation
      handler_input.response_builder\
        .speak('{} was awarded the Medal of Honor in {}<break time="600ms"/>{}'.format(name, year_of_honor, speech_text))\
        .set_card(
          StandardCard(name, speech_text, Image(img, img)))\
        .set_should_end_session(False)

      session_attributes = handler_input.attributes_manager.session_attributes
      session_attributes['last_request'] = {
        'name': name,
        'citation': citation,
        'img': img
      }

    return handler_input.response_builder.response

class RandomRecipientIntentHandler(AbstractRequestHandler):
  """Handler for Recipient Intent"""
  def can_handle(self, handler_input):
    # type: (HandlerInput) -> bool
    return is_intent_name("RandomRecipient")(handler_input)

  def handle(self, handler_input):
    # type: (HandlerInput) -> Response

    # fetch data into dynamodb
    logger.info('searching for a recipient in dynamodb')
    table = boto3.resource('dynamodb').Table('MedalOfHonorInfo')
    random_name = ''.join([random.choice(string.ascii_uppercase) for i in range(1,20)]).title()
    random_year = str(random.choice(range(1800, datetime.now().year)))
    response = table.scan(Limit=1, ExclusiveStartKey={'name': random_name, 'year_of_honor': random_year})

    print 'response={}'.format(response)

    citation = response['Items'][0]['citation']
    year_of_honor = response['Items'][0]['year_of_honor']
    img = response['Items'][0]['img']
    name = response['Items'][0]['name']
    speech_text = citation
    handler_input.response_builder\
      .speak('{} was awarded the Medal of Honor in {}<break time="600ms"/>{}'.format(name, year_of_honor, speech_text)) \
      .set_card(
        StandardCard(name, speech_text, Image(img, img)))\
      .set_should_end_session(False)

    session_attributes = handler_input.attributes_manager.session_attributes
    session_attributes['last_request'] = {
      'name': name,
      'citation': citation,
      'img': img
    }

    return handler_input.response_builder.response

class HelpIntentHandler(AbstractRequestHandler):
  """Handler for Help Intent"""
  def can_handle(self, handler_input):
    # type: (HandlerInput) -> bool
    return is_intent_name("AMAZON.HelpIntent")(handler_input)

  def handle(self, handler_input):
    # type: (HandlerInput) -> Response
    speech_text = 'This skill can give you more information about the Medal of Honor and its recipients. Try saying "Alexa, ask Medal of Honor Info what is the Medal of Honor?"'

    handler_input.response_builder\
      .speak(speech_text)\
      .ask(speech_text)\
      .set_card(
        SimpleCard("Medal of Honor Info", speech_text))

    session_attributes = handler_input.attributes_manager.session_attributes
    session_attributes['last_request'] = {
      'speech_text': speech_text
    }

    return handler_input.response_builder.response

class CancelOrStopIntentHandler(AbstractRequestHandler):
  """Single handler for Cancel and Stop Intent"""
  def can_handle(self, handler_input):
    # type: (HandlerInput) -> bool
    return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
            is_intent_name("AMAZON.StopIntent")(handler_input))

  def handle(self, handler_input):
    # type: (HandlerInput) -> Response
    speech_text = "Goodbye."

    handler_input.response_builder.speak(speech_text)
    return handler_input.response_builder.response

class FallbackIntentHandler(AbstractRequestHandler):
  """AMAZON.FallbackIntent is only available in en-US locale.
  This handler will not be triggered except in that locale,
  so it is safe to deploy on any locale.
  """
  def can_handle(self, handler_input):
    # type: (HandlerInput) -> bool
    return is_intent_name("AMAZON.FallbackIntent")(handler_input)

  def handle(self, handler_input):
    # type: (HandlerInput) -> Response
    speech_text = (
      'Sorry I can\'t help you with that.  '
      'Try saying "Alexa, ask Medal of Honor Info about a random recipient"')
    reprompt = 'Try saying "Alexa, ask Medal of Honor Info about a random recipient"'
    handler_input.response_builder\
      .speak(speech_text)\
      .ask(reprompt)
    return handler_input.response_builder.response

class SessionEndedRequestHandler(AbstractRequestHandler):
  """Handler for Session End."""
  def can_handle(self, handler_input):
    # type: (HandlerInput) -> bool
    return is_request_type("SessionEndedRequest")(handler_input)

  def handle(self, handler_input):
    # type: (HandlerInput) -> Response
    return handler_input.response_builder.response

class CatchAllExceptionHandler(AbstractExceptionHandler):
  """Catch all exception handler, log exception and
  respond with custom message.
  """
  def can_handle(self, handler_input, exception):
    # type: (HandlerInput, Exception) -> bool
    return True

  def handle(self, handler_input, exception):
    # type: (HandlerInput, Exception) -> Response
    logger.error(exception, exc_info=True)

    speech = "Sorry, there was some problem. Please try again!!"
    handler_input.response_builder.speak(speech).ask(speech)

    return handler_input.response_builder.response


sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(RepeatIntentHandler())
sb.add_request_handler(LatestRecipientIntentHandler())
sb.add_request_handler(WomenAwardedIntentHandler())
sb.add_request_handler(WhatIsItIntentHandler())
sb.add_request_handler(RecipientIntentHandler())
sb.add_request_handler(RandomRecipientIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()