import os
from random import getrandbits

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or str(getrandbits(128))
