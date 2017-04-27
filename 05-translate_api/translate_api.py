# encoding: utf-8
import urllib
import demjson

"""
Language Code
-------- ----
Afrikaans 	af
Albanian 	sq
Arabic 	ar
Belarusian 	be
Bulgarian 	bg
Catalan 	ca
Chinese Simplified 	zh-CN
Chinese Traditional 	zh-TW
Croatian 	hr
Czech 	cs
Danish 	da
Dutch 	nl
English 	en
Estonian 	et
Filipino 	tl
Finnish 	fi
French 	fr
Galician 	gl
German 	de
Greek 	el
Hebrew 	iw
Hindi 	hi
Hungarian 	hu
Icelandic 	is
Indonesian 	id
Irish 	ga
Italian 	it
Japanese 	ja
Korean 	ko
Latvian 	lv
Lithuanian 	lt
Macedonian 	mk
Malay 	ms
Maltese 	mt
Norwegian 	no
Persian 	fa
Polish 	pl
Portuguese 	pt
Romanian 	ro
Russian 	ru
Serbian 	sr
Slovak 	sk
Slovenian 	sl
Spanish 	es
Swahili 	sw
Swedish 	sv
Thai 	th
Turkish 	tr
Ukrainian 	uk
Vietnamese 	vi
Welsh 	cy
Yiddish 	yi
"""




API_KEY = 'key'

if len(API_KEY)<39:
    print("Warning this is a non fonctionnal api_key, input the correct key to activate service")

TRANSLATE_URL = "https://www.googleapis.com/language/translate/v2?key=" + API_KEY  # &q=hello%20world&source=en&target=de
DETECT_URL = "https://www.googleapis.com/language/translate/v2/detect?key=" + API_KEY  # &q=google+translate+is+fast


#Thanks to http://deron.meranda.us/python/demjson/ for the nice tutorial and package

def unicode_urlencode(params):
    if isinstance(params, dict):
        params = params.items()
    return urllib.urlencode([(k, isinstance(v, unicode) and v.encode('utf-8') or v) for k, v in params])


def send_request(url):
    return urllib.urlopen(url).read()


def quick_translate(text, target_lang, source_lang):
    try:
        return translate(text, target_lang, source_lang)["data"]["translations"][0]["translatedText"].replace('&#39;', "'")
    except:
        return ""


def translate(text, target_lang, source_lang):
    query_params = {"q": text, "source": source_lang, "target": target_lang}
    url = TRANSLATE_URL + "&" + unicode_urlencode(query_params)
    try:
        return demjson.decode(send_request(url))
    except:
        return {}


def quick_detect(text):
    try:
        return detect(text)["data"]["detections"][0][0]["language"]
    except:
        return ""


def detect(text):
    query_params = {"q": text}
    url = DETECT_URL + "&" + unicode_urlencode(query_params)
    try:
        return demjson.decode(send_request(url))
    except:
        return {}


