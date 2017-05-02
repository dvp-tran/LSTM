#!/usr/bin/env python
# -*- coding: utf-8 -*-

import twitter
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os, os.path
from os import listdir
from os.path import isfile, join
import urllib2
import time
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
import textwrap
import sys
import subprocess
import translate_api
from unicodedata import normalize


#variables:
#file_path="images/1.jpg"
nb_letters=700

#Credentials
api = twitter.Api(consumer_key='LyNVanTEQEOEGKfXAMeLv6AKG',
                    consumer_secret='0lJvhaaOP5cRZWm6rxwyBIAypd1P7eiDx9f74KBDlLrSldNuBQ',
                    access_token_key='855852332034265088-geTEVmA7xIsOD3WCZyfBNnqjRdS1MhW',
                    access_token_secret='kJMwMl67e3nYrqaGWzIizxzQpRZhtBfOnwPflO1fk3cOt')


print(api.VerifyCredentials())


# ## I. Bot sniffing

def get_timeline(count):
    timeline=api.GetHomeTimeline(count=count)
    return timeline

def get_reply(status_id,count):
    replies = api.GetReplies(status_id,count=count,trim_user=True)
    return replies

def get_media_reply(timeline, last=True):
    for statuses in timeline:
        if statuses.media and statuses.user.screen_name!=u'TheTalkativeBot':
            index=statuses.id
            user_name=statuses.user.screen_name
            media_url=statuses.media[0].media_url
            status_text=statuses.text
            if last==True:
                break
    return index,user_name,media_url,status_text

def save_media(media_url):
    DIR="../data/images/"
    try:
        onlyfiles = [f for f in listdir(DIR) if isfile(join(DIR, f))]
        nb_files = len(onlyfiles)
    except Exception as e:
        print(e)
        if not os.path.exists(DIR):
            os.makedirs(DIR)
        nb_files=0
    img = urllib2.urlopen(media_url)
        
    with open("../data/images/%s.jpg" %(nb_files+1), 'wb') as f:
        f.write(img.read())
    path="../data/images/%s.jpg" %(nb_files+1)
    return path

# ## II. Post media


def auto_answer(since_id=None):
    flag=True
    i=0
    while flag==True:
        try:
            time.sleep(10)
            print("Iteration : %s" %i)
            if not since_id:
                timeline=get_timeline(4)
                status_id,user,media_url,status_text = get_media_reply(timeline,last=True)                
            if not os.path.exists('../data/images/list/'):
                os.makedirs('../data/images/list/')
            with open('../data/images/list/list.txt','r') as f:
                text = f.read()
            text=text.split("\n")
            if media_url not in text:
                #saving image
                file_path=save_media(media_url)
                print("Image saved at : %s." %file_path)
                #detect language:
                lang="en"
                if "french" in status_text.lower():
                    lang="fr"
                if "german" in status_text.lower():
                    lang="ger"
                text_input=bot_evoke(file_path,nb_letters,lang)
                if not text_input:
                    print("Error in evoke step!")
                    flag=False
                #define outpath by parsing file_path
                out_path="../data/output/"+(file_path[15:])
                draw_answer(file_path,out_path,text_input)
                print("Answer-image drawn and saved at :%s!" %out_path)
                post_media(out_path,status_id)
                print("Status id : %s, answered." %status_id)
                with open('../data/images/list/list.txt', "a") as f:
                    f.write(media_url+"\n")
                print("Image flagged for no further repetition.")
            
                time.sleep(10)
            i=i+1
            time.sleep(60)
            if i==25:
                flag=False
                
        except Exception as e:
            print(e)
            if "Rate limit exceeded" in str(e):
                print("Sleeping  because of rate limit.")
                time.sleep(60)
                print("Restarting")
                
    return


# ## III. Create picture to send


def draw_answer(in_path,out_path,text_input):
    file_name=out_path
    img = Image.open(in_path)
    size = 600, 600
    text = text_input
    text=textwrap.wrap(text, width=50)

    try:
        img.thumbnail(size, Image.ANTIALIAS)
    except IOError:
        print "cannot create thumbnail for '%s'" % infile

    img_w, img_h = img.size
    background = Image.new('RGBA', (900, 1200), (255, 255, 255, 255))
    bg_w, bg_h = background.size
    offset = ((bg_w - img_w) / 2, (bg_h - img_h) / 6)
    background.paste(img, offset)
    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype("../data/font/SpecialElite.ttf", 30)
    # draw.text((x, y),"Sample Text",(r,g,b))
    offset_=0
    for line in text:
        w, h = draw.textsize(line, font=font)
        draw.text(((900-w)/2, 650+offset_),line,(0,0,0),font=font)
        offset_ += h+5

    background.save(file_name)
    print("Done drawing answer!")
    
    return


def post_media(media_path,post_id):
    api.PostUpdate("Here what's your picture evokes to me !",
                media=media_path, media_additional_owners=None,media_category=None,
               in_reply_to_status_id=post_id, auto_populate_reply_metadata=True,
               exclude_reply_user_ids=None, latitude=None, longitude=None, place_id=None,
               display_coordinates=False, trim_user=False, verify_status_length=True, attachment_url=None)
    print("Answer sent!")
    return


# ## IV. Generate text from image

def bot_evoke(file_path,nb_letters,lang):
    print("Image Captionning...")
    proc = subprocess.Popen(["python","generate_from_image.py",file_path], stdout=subprocess.PIPE)
    blabla = proc.communicate()[0]
    blabla = blabla.replace(" ."," ")
    print("\t" +blabla)
    if lang=="en":
        proc = subprocess.Popen(["python","english_lstm.py",blabla,"%s" %nb_letters], stdout=subprocess.PIPE)
        blabla = proc.communicate()[0]
        print(blabla)
        return blabla
    blabla = translate_api.quick_translate(blabla,lang,"en").encode('utf-8')
    blabla = normalize('NFKD',blabla.decode('utf-8')).encode('ASCII', 'ignore')
    print("\t Translation in %s :%s !" %(lang,blabla))
    print("Dreaming...")
    if lang=="fr":
        print("In french :")
        proc = subprocess.Popen(["python","french_lstm_2.py",blabla,"%s" %nb_letters], stdout=subprocess.PIPE) #french_lstm_2
        blabla = proc.communicate()[0]   
    if lang=="ger":
        proc = subprocess.Popen(["python","german_lstm.py",blabla,"%s" %nb_letters], stdout=subprocess.PIPE)
        blabla = proc.communicate()[0]  
    print(blabla)
    return blabla


