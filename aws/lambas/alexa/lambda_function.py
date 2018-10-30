import logging
import datetime

import boto3
from boto3.dynamodb.conditions import Key

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard
from ask_sdk_model.ui import StandardCard
from ask_sdk_model import Response

sb = SkillBuilder()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MEDAL_OF_HONOR_INFO = \
'The Medal of Honor is the United States of America\'s highest and most prestigious personal \
military decoration that may be awarded to recognize U.S. military service members who have \
distinguished themselves by acts of valor. The medal is normally awarded by the President of \
the United States in the name of the U.S. Congress.'

class LaunchRequestHandler(AbstractRequestHandler):
  """Handler for Skill Launch."""
  def can_handle(self, handler_input):
    # type: (HandlerInput) -> bool
    return is_request_type("LaunchRequest")(handler_input)

  def handle(self, handler_input):
    # type: (HandlerInput) -> Response
    speech_text = 'This skill can give you more information about the Medal of Honor and its recipients. Try saying "Alexa, ask Medal of Honor Info what is the Medal of Honor?"'

    handler_input.response_builder\
      .speak(speech_text)\
      .set_card(
        SimpleCard("Medal of Honor Info", speech_text))\
          .set_should_end_session(False)
    return handler_input.response_builder.response


class RepeatIntentHandler(AbstractRequestHandler):
  """Handler for Repeat Intent."""
  def can_handle(self, handler_input):
    # type: (HandlerInput) -> bool
    return is_request_type("RepeatIntent")(handler_input)

  def handle(self, handler_input):
    # type: (HandlerInput) -> Response
    #TODO: https://developer.amazon.com/blogs/alexa/post/2279543b-ed7b-48b4-a3aa-d273f7aab609/alexa-skill-recipe-using-session-attributes-to-enable-repeat-responses
    speech_text = 'This skill can give you more information about the Medal of Honor and its recipients. Try saying "Alexa, ask Medal of Honor Info what is the Medal of Honor?"'

    handler_input.response_builder\
      .speak(speech_text)\
      .set_card(
        SimpleCard("Medal of Honor Info", speech_text))\
          .set_should_end_session(False)
    return handler_input.response_builder.response


class LatestRecipientIntentHandler(AbstractRequestHandler):
  """Handler for Latest Recipient Intent"""
  def can_handle(self, handler_input):
    # type: (HandlerInput) -> bool
    return is_intent_name("LatestRecipient")(handler_input)

  def handle(self, handler_input):
    # type: (HandlerInput) -> Response

    # fetch data into dynamodb
    logger.info('searching for latest recipent in dynamodb')
    table = boto3.resource('dynamodb').Table('MedalOfHonorInfo')
    min_year = str(datetime.datetime.now().year - 5) # assume that the award will be given out at least every 5 years
    # TODO response = table.scan(FilterExpression=Key('year_of_honor').gt(min_year))
    response = table.scan(FilterExpression=Key('year_of_honor').gt('1969'))
    print 'response={}'.format(response)

    # find recorded with greatest year_of_honor. there isn't much we can do about tie-breaking
    newest = max(response['Items'], key=lambda val: val['year_of_honor'])
    print 'newest={}'.format(newest)

    citation = response['Items'][0]['citation']
    # year_of_honor = response['Items'][0]['year_of_honor']
    img = response['Items'][0]['img']
    name = response['Items'][0]['name']
    speech_text = citation
    handler_input.response_builder\
      .speak(speech_text)\
      .set_card(
        # TODO StandardCard(name, speech_text, img))\
        SimpleCard(name, speech_text))\
          .set_should_end_session(False)

    return handler_input.response_builder.response

class RecipientIntentHandler(AbstractRequestHandler):
  """Handler for Recipient Intent."""
  def can_handle(self, handler_input):
    # type: (HandlerInput) -> bool
    return is_intent_name("RecipientIntent")(handler_input)

  def handle(self, handler_input):
    # type: (HandlerInput) -> Response

    slots = handler_input.request_envelope.request.intent.slots
    recipient = slots['recipient'].value
    recipient = recipient.title()

    # fetch data into dynamodb
    print 'searching for {} in dynamodb'.format(recipient)
    table = boto3.resource('dynamodb').Table('MedalOfHonorInfo')
    response = table.query(KeyConditionExpression=Key('name').eq(recipient), Limit=1)
    print 'response={}'.format(response)

    if len(response['Items']) == 0:
      speech_text = 'There are no Medal of Honor recipients by the name of {}'.format(recipient)
      handler_input.response_builder.speak(speech_text)
    else:
      citation = response['Items'][0]['citation']
      # year_of_honor = response['Items'][0]['year_of_honor']
      img = response['Items'][0]['img']
      name = response['Items'][0]['name']
      speech_text = citation
      handler_input.response_builder\
        .speak(speech_text)\
        .set_card(
          # TODO StandardCard(name, speech_text, img))\
          SimpleCard(name, speech_text)) \
        .set_should_end_session(False)

    return handler_input.response_builder.response

class HelpIntentHandler(AbstractRequestHandler):
  """Handler for Help Intent."""
  def can_handle(self, handler_input):
    # type: (HandlerInput) -> bool
    return is_intent_name("AMAZON.HelpIntent")(handler_input)

  def handle(self, handler_input):
    # type: (HandlerInput) -> Response
    speech_text = 'This skill can give you more information about the Medal of Honor and its recipients. Try saying "Alexa, ask Medal of Honor Info what is the Medal of Honor?"'

    handler_input.response_builder.speak(speech_text).ask(
      speech_text).set_card(SimpleCard(
      "Medal of Honor Info", speech_text))
    return handler_input.response_builder.response


class CancelOrStopIntentHandler(AbstractRequestHandler):
  """Single handler for Cancel and Stop Intent."""
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
    handler_input.response_builder.speak(speech_text).ask(reprompt)
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
sb.add_request_handler(RecipientIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()