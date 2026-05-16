import json
from datetime import datetime
import requests

from inngest.exceptions import InngestException


class Event:
  def __init__(self, name=None, data=None, user=None, version=None, timestamp=None):
    self.name = name
    self.data = data
    self.user = user
    self.version = version
    self.timestamp = timestamp if timestamp else int(datetime.now().timestamp() * 1000)

  def payload(self):
    data = {
      'name': self.name,
      'data': self.data,
      'user': self.user,
      'v': self.version,
      'ts': self.timestamp,
    }
    return {k: v for k, v in data.items() if v is not None}


class InngestClient:
  API_ENDPOINT = "https://inn.gs"
  HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': 'inngest-python-sdk/1.0.0',
  }

  def __init__(self, inngest_key=None, endpoint=API_ENDPOINT):
    self.inngest_key = inngest_key
    self.endpoint = endpoint
    self.session = requests.session()

  def send(self, event):
    validate_event(event)
    validate_inngest_key(self.inngest_key)

    url = "{endpoint}/e/{key}".format(
      endpoint=self.endpoint,
      key=self.inngest_key
    )
    return self.session.post(
      url,
      headers=self.HEADERS,
      json=event.payload()
    )


def validate_event(event):
  if not event:
    raise InngestException("Event can't be `None`")

  if not event.name or not event.name.strip():
    raise InngestException("Event name can't be empty")

  if not event.data:
    raise InngestException("Event data is invalid")

  try:
    json.dumps(event.data)
  except Exception:
    raise InngestException("Could not serialize data into json")


def validate_inngest_key(inngest_key):
  if not inngest_key:
    raise InngestException("Inngest key was not specified")
