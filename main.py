from nutrition_network import predict
import glob
import os
import sys
import time
import requests
import json
import vk_api
import telebot
import threading
import re
import random
import urllib.request, gzip
from PIL import Image
from PIL.BufrStubImagePlugin import register_handler
from telebot import types
from telebot.types import InputMediaPhoto, InputMediaDocument
from logger import get_logger

