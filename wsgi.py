# Thinking base python app with bootstrap ect to run
import requests
import ssl
import os
import time
import random
import pytz
import aiohttp
from flask import Flask, render_template, request, json, jsonify, send_from_directory, url_for, redirect, session

app = Flask(__name__,
static_folder='static',
static_url_path='/static',
template_folder='templates')

app.secret_key = os.urandom(12).hex()
app.config['DEBUG'] = True
app.logger.info('Started QA')

@app.route('/')
def return_index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run()