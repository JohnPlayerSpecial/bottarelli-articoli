#http://www.ilsussidiario.net/Feed/autore/230/Mauro-Bottarelli/
from bs4 import BeautifulSoup
from newspaper import Article
import feedparser
from telegraphapi import Telegraph
import telegram
from telegram.error import *
import os
import urllib.request
import requests
from telegram.ext import *
import time
import datetime
from datetime import timedelta
from mercury_parser.client import MercuryParser
from telegraphapi import Telegraph
from newspaper import Article
from urllib.request import urlopen 
import postgresql

STRING_DB = os.environ['DATABASE_URL'].replace("postgres","pq")
API_KEY_MERCURY_PARSER = os.environ['API_KEY_MERCURY_PARSER']  
TOKEN_TELEGRAM = os.environ['TOKEN_TELEGRAM'] 
MY_CHAT_ID = int( os.environ['MY_CHAT_ID'] )
HOUR_I_WANNA_GET_MESSAGE = int( os.environ['HOUR_I_WANNA_GET_MESSAGE'] )
MINUTES_I_WANNA_GET_MESSAGE = int( os.environ['MINUTES_I_WANNA_GET_MESSAGE'] )

parser = MercuryParser(api_key = API_KEY_MERCURY_PARSER)
feed = 'http://www.ilsussidiario.net/Feed/autore/230/Mauro-Bottarelli/'
telegraph = Telegraph()
telegraph.createAccount('TELEGRAPH_ACCOUNT')

def init_DB():
	global STRING_DB
	db = postgresql.open(STRING_DB)
	ps = db.prepare("CREATE TABLE IF NOT EXISTS url (id serial PRIMARY KEY, url varchar(300) unique);")
	ps()          
	db.close()

def getArticles( bot, job ):
	global STRING_DB
	db = postgresql.open(STRING_DB)
	ps = db.prepare("SELECT * FROM url;")
	allUrl = [ item[1] for item in ps() ]
	entries = feedparser.parse( feed ).entries
	for post in entries:
		if post.link not in allUrl:
			try:
				ps = db.prepare("INSERT INTO url (url) VALUES ('{}') ON CONFLICT (url) DO NOTHING;".format(post.link) )
				ps()
				#print(post.link)
				article = parser.parse_article( post.link )
				title = article.json()['title'].replace("SPY FINANZA/ ","")
				lead_image_url = article.json()['lead_image_url']
				excerpt = article.json()['excerpt']
				word_count = article.json()['word_count']
				content = article.json()['content']
				article = Article( post.link )
				article.download()
				article.parse()
				text = article.text
				#print(text)
				articleImage = article.top_image
				articleTitle = article.title.replace("SPY FINANZA/ ","")
				articleUrl = article.url
				html = urlopen( post.link )
				html_content = BeautifulSoup( html , 'html.parser' ).findAll("p", {"style":"text-align: left;"})
				contentWithImages = ''
				for item in html_content:
					contentWithImages += str(item).replace("<span>","").replace('<span class="s1">',"").replace('</span>',"")

				contentWithImages = '<a href="{}"><img src="{}"/></a>'.format(articleImage, articleImage) + contentWithImages
				#print(contentWithImages)

				page = telegraph.createPage( title = title,  html_content = contentWithImages , author_name = "Mauro Bottarelli" )
				url2send = 'http://telegra.ph/' + page['path']
				published = post.published
				datePub = published.replace("+0200","")

				text = '<a href="{}">{}</a><b>{}</b>\n<i>{}</i>\n\n<b>{} parole, {} minuti ca. di lettura\n</b>Pubblicato {} da <a href="{}">ilsussidiario.net</a>\n{}'.format( url2send, u"\u2063", articleTitle, excerpt.replace("MAURO BOTTARELLI","Mauro Bottarelli"), word_count, int(word_count/235), datePub, post.link, u"\u2063" )
				bot.sendMessage(chat_id=MY_CHAT_ID, text = text, parse_mode = "Html")
				time.sleep(0.1)
			except Exception as e:
				print(e)
		else:
			pass
			
def start( bot, update ):
	bot.sendMessage(chat_id = update.message.chat_id, text = "Successfully subscribed.")

init_DB()
updater = Updater(TOKEN_TELEGRAM) 
dp = updater.dispatcher
updater.dispatcher.add_handler(CommandHandler('start', start))

j = updater.job_queue
utc_offset_heroku = time.localtime().tm_gmtoff / 3600

hour = HOUR_I_WANNA_GET_MESSAGE + ( int(utc_offset_heroku) - 2 ) # 2 is my offset
time2 = datetime.time(hour , MINUTES_I_WANNA_GET_MESSAGE)
time3 = datetime.time(hour + 12 , MINUTES_I_WANNA_GET_MESSAGE)
j.run_daily(getArticles, time2 )
j.run_daily(getArticles, time3 )
updater.start_polling()
updater.idle()
