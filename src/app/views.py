import wikipedia
from AI.get_def import get_def
from AI.test import prediction
from AI.wiki import search_on_wikipedia
from AI.word_extraction import word_extraction
from flask import request
from googletrans import Translator
from scrapper.data_scrapper import data_scrapping
import os
from dotenv import load_dotenv
from app import app

load_dotenv()
def get_lang(g_words):
	word = Translator().translate(g_words, dest='en')
	return str(word.src)
def json_body_check(req, type):
    if not req:
        return { "e" }
    if type not in req:
        return { "e" }   
    if req.get("api_key", False) != os.getenv("API_KEY"):       
        return { "e" }


@app.route('/suggest-articles', methods=['POST'])
def sa():
    if json_body_check(request.json, "text") == { "e" }:
        return {"error": "invalid request"}

    txt = request.json['text']
    kw = []
    lang = get_lang(txt)
    wikipedia.set_lang(lang)
    keywords = word_extraction(str(txt), lang)

    for i in keywords:
        if i[1]<=0.09:
        	kw.append(i[0])
    recommended_articles = search_on_wikipedia(kw, lang) 
    
    return {
			"keywords": kw,
			"recommended_articles": recommended_articles
		  }


@app.route('/ai-tips', methods=['POST'])
def at():
    if json_body_check(request.json, "word") == { "e" }:
        return { "error": "invalid request" }

    word = request.json['word']
    word = str(word)
    word = word.replace('_', ' ')
    out = {}
    if len(word.split()) == 1:
        try:
        	definition, lang = get_def(word)
        	wikipedia.set_lang(lang) 
        except:
            definition = ""
            lang = get_lang(word)
        out["definition"] = definition
    else:
    	lang = get_lang(word)

    recommended_articles = wikipedia.search(word)
    websites_url = []

    for c in recommended_articles:
        article = c
        article = article.replace(' ', '_')
        tmp = "https://" + lang + '.wikipedia.org/wiki/' + article
        websites_url.append(tmp)

    try:
        kw = []
        url = 'https://' + lang + '.wikipedia.org/wiki/' + recommended_articles[0]
        scrapped_data = data_scrapping(url)
        output = prediction(scrapped_data["output"], 3)
        if "error" in scrapped_data:
            return {"error": "Website does not allow scrapping"}

        keywords = word_extraction(str(output), lang)
        for i in keywords:
            if i[1]<=0.09:
                kw.append(i[0])
    except:
        output = None
        kw = []
        recommended_articles = []

    return {
            "output": output,
			"keywords": kw,
			"recommended_articles": websites_url
		}


@app.route('/summarize-text', methods=['POST'])
def st():
    if json_body_check(request.json, "text") == { "e" }:
        return {"error": "invalid request"}

    length = 5
    if "length" in request.json:
        length = request.json['length']

    doc = request.json['text']
	
    output = prediction(doc, length)
	
    out = {
    	"output": output
    }

    kw = []
    if request.json.get("keywords", False):
        lang = get_lang(output[0])
        wikipedia.set_lang(lang) 
        keywords = word_extraction(str(output), lang) #TODO : get language
        for i in keywords:
            if i[1]<=0.09:
                kw.append(i[0])
        out["keywords"] = kw

        recommended_articles = search_on_wikipedia(kw, lang)
        out["recommended_articles"] = recommended_articles

    return out


@app.route('/summarize-url', methods=["POST"])
def su():
    if json_body_check(request.json, "url") == { "e" }:
        return { "error": "invalid request" }
    url = request.json["url"]

    length = 5
    if "length" in request.json:
        length = request.json['length']

    scrapped_data = data_scrapping(url)
    if "error" in scrapped_data:
        return {"error": "Website does not allow scrapping"}

    output = prediction(scrapped_data["output"], length)
    out = { "output": output }
    kw = []

    if request.json.get("keywords", False):
        lang = get_lang(output[0])
        wikipedia.set_lang(lang) 
        keywords = word_extraction(str(output), lang) #TODO: get language
        for i in keywords:
            if i[1]<=0.09:
                kw.append(i[0])
        out["keywords"] = kw

        recommended_articles = search_on_wikipedia(kw, lang)
        out["recommended_articles"] = recommended_articles

    return out    


if __name__ == "__main__":
	app.run(host='0.0.0.0', debug=True, port=80)