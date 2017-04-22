# -*- coding: utf-8 -*-

import os, sys, json, re, argparse, urllib2, html5lib
from bs4 import BeautifulSoup, Tag, UnicodeDammit
import pandas as pd
from pandas.io.json import json_normalize
import time
from collections import Counter


def get_script(url):
    #load script
    script_url = url
    is_webpage_fetched = False
    request_headers = {
    "Accept-Language": "en-US,en;q=0.5",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",
    #"Connection": "keep-alive" 
    }


    while not is_webpage_fetched:
        # get the script's URL from the parameters if it was passed
        try:
            request = urllib2.Request(script_url, headers=request_headers)
            contents = urllib2.urlopen(request)#.read()
            soup = BeautifulSoup(contents, 'lxml')
            #print('Detected encoding is ', soup.original_encoding)
            is_webpage_fetched = True
        except urllib2.URLError as err:
            print('Catched an URLError while fetching the URL:', err)
            pass
        except ValueError as err:
            print('Catched a ValueError while fetching the URL:', err)
            pass
        except:
            print('Catched an unrecognized error')
            raise
        else:
            #script_text = soup.find("td", class_="scrtext").find("pre")
            script_text = soup.find("pre")

            if( script_text.find("pre") ):
                print('Found a <pre> inside the <pre>')
                script_text = script_text.find("pre")
            is_webpage_fetched = True
    print('Getting script @ %s.' %(url))
    return script_text,soup



def white_space_analysis(script_text,soup):
    spaces_regex = re.compile("^(\s*).*")
    space_vector=[]
    character_presence=[]

    for block in script_text.descendants:
        # Si block est une instance de bs4.Tag, il est entouré de balises HTML
        # Le prochain block contiendra le même texte sans les balises
        # Donc on continue sans parser ce bloc
        if(isinstance(block, Tag)):
            continue

        # UnicodeDammit converts any string to UTF-8
        # does not work so well
        block = UnicodeDammit(block, soup.original_encoding).unicode_markup
        # remove leading and ending end of lines
        block = block.strip('\n').strip('\r\n')

        # if the block doesn't have any text, skip it
        if( re.search('\w', block) == None ):
            continue

        for line in block.split('\n'):
            stripped_line = line.strip(' \n\t\r')
            if( re.search('\w', line) == None ):
                continue    
            # Counting the number of spaces at the beginning of the line
            spmatch = spaces_regex.search(line)
            space_vector.append(len(spmatch.group(1)))
            if (stripped_line.isupper()) & (len(stripped_line.split(' '))<=3):
                character_presence.append(len(spmatch.group(1)))

            else:
                character_presence.append(None)
                                            


            
    return space_vector,character_presence #,speech_presence


def identify_usual_spaces(space_vector,character_presence):
    #identify space for characters
    c=Counter([a for a in character_presence if a])
    char=sorted(c,key=c.get,reverse=True)[0]
    #identify space for speech
    indexes=[index+1 for index, value in enumerate(space_vector) if value == char]
    del indexes[-1]
    speech_presence=[space_vector[a] for a in indexes]
    c=Counter([a for a in speech_presence if a])
    speech=sorted(c,key=c.get,reverse=True)[0]
    #compute ratio
    a=Counter(space_vector)
    other=Counter([e for e in space_vector if e!=char and e!=speech])
    b=sorted(other,key=other.get,reverse=True)
    ratio=float((a[char]+a[speech]+a[b[0]]+a[b[1]]))/float(len(space_vector))
    #print(ratio)
    if ratio > 0.9:
        usual_spaces=[[char],[speech],[b[0]],[b[1]],[]]
        return  usual_spaces,True
    else:
        print('This script is too unstable to parse')
        usual_spaces=[[char],[speech],[b[0]],[b[1]],[]]
        return usual_spaces,False

    
    
def write_csv(data,name,path):
    #if folder does not exist
    if not os.path.exists(path):
        os.makedirs(path)
    data.to_csv('%s%s.csv' %(path,name),sep='|',encoding='latin1')
    return

def get_line_type(line, stripped_line, usual_spaces):
    # Counting the number of spaces at the beginning of the line
    spaces_regex = re.compile("^(\s*).*")
    location_regex = re.compile("^\s*(INT\.|EXT\.)")
    BLOCK_TYPES=['character', 'speech', 'stage direction', 'location','unknown']
    CHARACTER=0
    SPEECH=1
    DIRECTIONS=2
    LOCATION=3
    
    spmatch = spaces_regex.search(line)
    spaces_number = len(spmatch.group(1))
    block_type = 4

    if( location_regex.search(line) != None ):
        #print('location')
        return LOCATION

    #if stripped_line in characters:
        #print(character)
        #return CHARACTER

    # Look for space
    for block_type_usual_spaces in usual_spaces:
        if spaces_number in block_type_usual_spaces:
            block_type = usual_spaces.index(block_type_usual_spaces)
            #print('We consider {:d} leading spaces as a \'{:s}\' block.'.format(
            #      spaces_number, BLOCK_TYPES[block_type]))
            #print(BLOCK_TYPES[block_type])
            return usual_spaces.index(block_type_usual_spaces)
            

      
    #print('failure for identifying : %s categorizing it as unknown' %(repr(line)))
    return block_type #return code 5 for unknown    
    
    
def parse(url,path,name):
    #init variables
    spaces_regex = re.compile("^(\s*).*")
    location_regex = re.compile("^\s*(INT\.|EXT\.)")

    BLOCK_TYPES=['character', 'speech', 'stage direction', 'location','unknown']
    CHARACTER=0
    SPEECH=1
    DIRECTIONS=2
    LOCATION=3
    
    time_start=time.time()
    
    if url.endswith('.pdf'):
        print('The file @ %s is a PDF' %(url))
        return
    
    script_text,soup=get_script(url)
    #write raw file:
    if not os.path.exists(path+'raw/'):
        os.makedirs(path+'raw/')
    with open(path+'raw/'+"%s.txt" %name, "w") as text_file:
        text_file.write(str(script_text))
    #####
    
    space_vector,character_presence = white_space_analysis(script_text,soup)
    usual_spaces,flag=identify_usual_spaces(space_vector,character_presence)

    # Ici on définit les variables qu'on remplira de texte
    is_intro = True
    movie_script = []
    intro = []
    last_line_type = -1
    last_character = 'unknown'
    text = []
    characters=[]

    for block in script_text.descendants:
        # Si block est une instance de bs4.Tag, il est entouré de balises HTML
        # Le prochain block contiendra le même texte sans les balises
        # Donc on continue sans parser ce bloc
        if(isinstance(block, Tag)):
            continue

        # UnicodeDammit converts any string to UTF-8
        # does not work so well
        block = UnicodeDammit(block, soup.original_encoding).unicode_markup
        # remove leading and ending end of lines
        block = block.strip('\n').strip('\n\r')

        # if the block doesn't have any text, skip it
        if( re.search('\w', block) == None ):
            continue

        for line in block.split('\n'):
            stripped_line = line.strip(' \n\t\r')
            if( re.search('\w', line) == None ):
                continue    
            # Counting the number of spaces at the beginning of the line
            spmatch = spaces_regex.search(line)
            space_vector.append(len(spmatch.group(1)))
            #print(block)
            #print(line)
            #print(len(spmatch.group(1)))
            line_type = get_line_type(line, stripped_line, usual_spaces)
            #print(line_type)
            #print(line)

            if(last_line_type == -1 # -1 = not initialized
               or last_line_type == line_type):
                text.append(stripped_line)
            else:
                if(last_line_type == CHARACTER):
                    last_character='\n'.join(text) #regex to supress (parenthesis) & replicate speaker
                    if not last_character in characters:
                        characters.append(last_character)
                elif(last_line_type == SPEECH):
                    movie_script.append({
                        'type': BLOCK_TYPES[last_line_type],
                        BLOCK_TYPES[CHARACTER]: last_character,
                        'text': '\n'.join(text)})
                    #print('We just parsed this JSON block:')
                    #print(movie_script[-1])
                else:
                    movie_script.append({
                        'type': BLOCK_TYPES[last_line_type],
                        'text': '\n'.join(text)})
                    #print('We just parsed this JSON block:')
                    #print(movie_script[-1])
                text=[stripped_line]

            last_line_type = line_type
            #print('----------------')

    result = json_normalize(movie_script)
    if flag:
        write_csv(result,name,path)
        print('      Done parsing script at %s in %s' %(url,time.time()-time_start))
        print('-----------------')
        return(result)
    else:
        path=path+'doubtful/'
        write_csv(result,name,path)
        print('      Done parsing script at %s in %s' %(url,time.time()-time_start))
        print('-----------------')
        return(result)
    
    



