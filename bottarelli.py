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


API_KEY_MERCURY_PARSER = 'nGc0ya2J7z2aalFrGa8Gx3Q1o8grGFsn3cz58EJy'
parser = MercuryParser(api_key = API_KEY_MERCURY_PARSER)

feed = 'http://www.ilsussidiario.net/Feed/autore/230/Mauro-Bottarelli/'
TOKEN_TELEGRAM = '423757798:AAF2T68VYPWcw9-t06qV6vcXvvNkMRMIROg'

telegraph = Telegraph()
telegraph.createAccount('TELEGRAPH_ACCOUNT')

def getArticles( bot, job ):
	entries = feedparser.parse( feed ).entries
	for post in tqdm(entries):
		try:
			print(post.link)
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
			dictDays = { "Mon" : "Lunedì",
			             "Tue" : "Martedì",
			             "Wed" : "Mercoledì",
			             "Thu" : "Giovedì",
			             "Fri" : "Venerdì",
			             "Sat" : "Sabato",
			             "Sun" : "Domenica",		     
			           }
			dictMonths = {  "Jan" : "Gennaio",
			                "Feb" : "Febbraio",
			                "Mar" : "Marzo",
			                "Apr" : "Aprile",
			                "May" : "Maggio",
			                "Jun" : "Giugno",
			                "Jul" : "Luglio",	
			                "Aug" : "Agosto",	
			                "Sep" : "Settembre",	
			                "Oct" : "Ottobre",	
			                "Nov" : "Novembre",	
			                "Dec" : "Dicembre",		     
			           }
			published = post.published
			datePub = published.replace("+0200","")
			
			text = '<a href="{}">{}</a><b>{}</b>\n<i>{}</i>\n\n<b>{} parole, {} minuti ca. di lettura\n</b>Pubblicato {} da <a href="{}">ilsussidiario.net</a>\n{}'.format( url2send, u"\u2063", articleTitle, excerpt.replace("MAURO BOTTARELLI","Mauro Bottarelli"), word_count, int(word_count/235), datePub, post.link, u"\u2063" )
			bot.sendMessage(chat_id=31923577, text = text, parse_mode = "Html")
			time.sleep(0.1)
		except Exception as e:
			print(e)
			
def start( bot, update ):
	bot.sendMessage(chat_id = update.message.chat_id, text = "Successfully subscribed.")

updater = Updater(TOKEN_TELEGRAM) 
dp = updater.dispatcher
updater.dispatcher.add_handler(CommandHandler('start', start))

j = updater.job_queue


utc_offset_heroku = time.localtime().tm_gmtoff / 3600

future = datetime.datetime.now() + timedelta(seconds=1) 

time2 = datetime.time(future.hour, future.minute, future.second)
print(time2)
j.run_daily(getArticles, time2 )

updater.start_polling()
updater.idle()
