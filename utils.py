# python3 -m venv ~/venv/
# source ~/venv/bin/activate

import llama_index
from llama_index.core import SQLDatabase
from llama_index.core.indices.struct_store import SQLStructStoreIndex
from llama_index.core.query_engine import NLSQLTableQueryEngine
# from llama_index.llms.openai import OpenAI
import openai
from openai import OpenAI
from sqlalchemy import create_engine
import os
import pymysql
import os
import re
import json
from datetime import datetime
import uuid

import json

import base64
from openai import OpenAI
from credentials import *

# Function to encode the image
def encode_image(image_path):
	with open(image_path, "rb") as image_file:
		return base64.b64encode(image_file.read()).decode("utf-8")

def load_wines_from_image(image_path, prompt=None):
	print("Reading menu...")
	base64_image = encode_image(image_path)
	load_wines_from_encoded_image(base64_image, prompt)

def load_wines_from_encoded_image(base64_image, prompt=None):	
	
	content = []
	if prompt is not None:
		logger.info(f"got a prompt: {prompt}")
		content.append({"type": "text", "text": prompt})

	content.append({
		  "type": "image_url",
		  "image_url": {
			"url": f"data:image/jpeg;base64,{base64_image}",
		  },
		})
	response = openai_client.chat.completions.create(
	  model="gpt-4o",
	  response_format={ "type": "json_object" },
	  messages=[
		{"role": "system", "content": "This is a wine menu. Return all wines shown as a structured JSON object." },
		{
		  "role": "user",
		  "content": content,
		}
	  ]
	)

	content = response.choices[0].message.content
	print(content)
	return content

def select_best_wine_from_image(image_path, wine_ratings):
	base64_image = encode_image(image_path)
	wine_data_string = json.dumps(wine_ratings, indent=4, sort_keys=True, default=str)
	response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[
    {
    	"role" : "user",
		"content": [
        	{"type": "text", "text": f"Recommend a new wine from the image. Use this historical tasting data as a guide for my preferences, but do not select one of these as your recommendation (ratings are on a 10 point scale): \n{wine_data_string}\n"},
			{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
			]
		}
	])

	content = response.choices[0].message.content
	print(content)
	return content

def general_image_upload_image(image_path, wine_ratings, prompt=None):
	base64_image = encode_image(image_path)
	general_image_upload_base64_encoded_image(base64_image, wine_ratings)

# NOTE: Not doing anything with prompt right now
def general_image_upload_base64_encoded_image(base64_image, wine_ratings, prompt=None):	
	wine_data_string = json.dumps(wine_ratings, indent=4, sort_keys=True, default=str)
	response = openai_client.chat.completions.create(
    model="gpt-4o",
    response_format={ "type": "json_object" },
    messages=[
    {
    	"role" : "user",
		"content": [
        	{"type": "text", "text": f"""

				You are Robert Parker a renown wine connoisseur and reviewer. 
				You are helping me select wines. I'm a Male in San Francisco, California.

				You will be given an image. First, classify the image into one of the following categories:
				- "wine_menu": A photo of a wine menu, typically containing a list of wines and prices.
				- "wine_label": A close-up photo of a wine bottle label, which may contain brand, grape type, and region.
				- "food": A photo of food, possibly a dish at a restaurant.

				If there are multiple wine labels, treat it like "wine_menu", not "wine_label".

				Respond in the following JSON format:
				{{
				  "category": "wine_menu" | "wine_label" | "food",
				  "title" : <a short header that describes your response. E.g. Pasta Pairing Suggestion>,
				  "query" : "image",
				  "analysis": <your analysis based on the category>,
				  "reasoning" : <Include your reasoning through the lens of what the experience of the wine would be. Don't use relative ratings. 
				  				 For example, good explaination would include "This wine has rich oaky wines from california with strong tannins, which you rate highly." 
				  				 A bad explaination would include "You rank california cabernets around 7.6."
				  				 2-4 sentences. Explain why I would be interested (or not) in this wine. What might I taste or think about while tasting? Be as specific as possible.>
				}}

				### **Analysis Instructions**
				- If the category is "wine_menu":
				  - Extract a complete list of wines and prices. Use the analysis["wines"] key.
				  - Based on the wine ratings provided below, predict the one I would like the most. Simply quote the wine name using the analysis["prediction"] key. No explaination.
				- If the category is "wine_label":
				  - Extract the structured data from the wine label as well as the color of the wine, if visible.
				  - Use the structured data to create a natural language description of the wine, (e.g. name with varietal, region, and vintage) as a single string. Use the analysis["wines"] key.
				  - Based on the wine ratings provided below, use the structured data to estimate the score I would give it, on a 10 point scale. Simply return a 1 point range (e.g. 6.5-7.5) as a string using the analysis["prediction"] key.
				- If the category is "food":
				  - Identify the dish or key ingredients. Use the analysis["dish"] key.
				  - Suggest a wine pairing for the dish. Go from broad to specific (e.g. dry white, from australia, a brand that offers dry whites from australia). Use the analysis["pairing"] key.

				### **Previous Wine Ratings**
        		Use this historical tasting data as a guide for your recommendations, but do not select one of these as your recommendation (ratings are on a 10 point scale): \n{wine_data_string}\n

        	"""},
			{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
			]
		}
	])

	content = response.choices[0].message.content
	print(content)
	return content	

# Try this again
# def select_best_wine_from_image(image_path, wine_ratings):
# 	base64_image = encode_image(image_path)
# 	wine_data_string = json.dumps(wine_ratings, indent=4, sort_keys=True, default=str)
# 	response_multimodal = openai_client.responses.create(
# 	    #model="gpt-4o",
# 		model="o3-mini",
# 		reasoning = { "effort"  : "low" },
# 		instructions = f"Recommend a new wine from the image. Use this historical tasting data as a guide for my preferences, but do not select one of these as your recommendation (ratings are on a 10 point scale): \n{wine_data_string}\n",
# 		text = { "format" : { "type": "json_object" } },
# 	    input=[
# 	        {
# 	            "role": "user",
# 	            "content": [
# 	                {"type": "input_text", "text": 
# 	                 f"Which wine from the image would I like the best based on my tasting data? Return answer as JSON."},
# 	                # {"type": "input_image", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}}
# 	            ]
# 	        }
# 	    ],
# 	    tools=[
# 	        {"type": "web_search"} # This can be used with 4o
# 	    ]
# 	)
# 	print(json.dumps(response_multimodal.__dict__, indent=4, sort_keys=True, default=str))


def get_buy_link(wine_descr):
	try:
		query = f"Find a reliable buy link for {wine_descr}. Only the link, no text."
		response = openai_client.responses.create(
            model="gpt-4o-mini",
            tools=[{"type": "web_search_preview"}],
            input=query
        )
		str_response = response.output[1].content[0].text
		print(f"Buy link : {str_response}")
		return str_response
	except openai.RateLimitError:
		print("Rate limit hit! Waiting before retrying...")
		time.sleep(10)  # Wait before retrying


def summarize_my_prefs(structured_wines):
	try:
		wine_data_string = json.dumps(structured_wines, indent=4, sort_keys=True, default=str)
		response = openai.chat.completions.create(
			model="o3-mini",
			reasoning_effort="medium", #"high",
			messages=[{"role": "system", "content": f"""You are Robert Parker a renown wine expert and reviewer. 
			You will be given my wine tasting data. I'm a Male in San Francisco, California.
			Given the data that is provided, I'd like you to create a profile by following these steps:
			1. Note which varietals, tags, regions, etc. are associated with high ratings.
			2. Asess any sentiment associated in the tasting notes.
			3. Consider when the wine was tasted and where the regions are in relation to the user and each other.
			4. Consider if there are any other factors such as food pairing, price, etc.
			5. Finally, create a "profile" for the user that hypothesizes their tastes, and models how a new wine might be reviewed.

			Summarize your results as a concise "wine taster profile" that you could give to a sommelier who would recommend the best wine.
			The summary should have 3 parapgrahs, 2-3 setences each: 
				1. Summarize the styles that I prefer and why.
				2. Summarize how I choose those styles, drawing from the tasting notes as well as your expert knowledge of those wines / regions / etc..
				3. Summarize where the drinker might expand, including new styles, regions, profiles, etc.
			The profile should be complementary but also assume I want to grow as a taster, in both depth and breadth.
			Under each paragraph suggest a wine, setting, pairing, or comparative tasting meditation that supports 
			the thesis presented in the paragraph.
			"""
			},
			{"role": "user", "content": wine_data_string}]
		)
		str_response = response.choices[0].message.content
		print("Profile:")
		print(str_response)		
		return str_response
	except openai.RateLimitError:
		print("Rate limit hit! Waiting before retrying...")
		time.sleep(10)  # Wait before retrying

def predict_wine_rating(nl_wine_string, structured_wines):
	try:
		wine_data_string = json.dumps(structured_wines, indent=4, sort_keys=True, default=str)
		user_message = f"""
			New Wine: "{nl_wine_string}"
			Historical Tasting Data:
			{wine_data_string}
		"""
		response = openai.chat.completions.create(
			model="o3-mini",
			reasoning_effort="low", #"medium", #"high",
			response_format={ "type": "json_object" },
			messages=[{"role": "system", "content": f"""You are a world famous sommelier, renown for your intuition and predictive powers. 
			I am a wine drinker who lives in San Francisco, California and I wan't you to help me decide on a wine by estimating how much I would like it.
			You will be provided with my "historical wine tasting data." 
			In this data, the "rating" value is on a 10-point scale.
			You will also be given an unstructured string that describes a "new wine" that I have not tasted. It may contain a rating in the 100 point scale.			
			Given the tasting data that is provided, I'd like you to estimate what my 10-point rating would 
			be for the new wine provided. Your estimate should be a range that expresses high confidence using the values "rating_range_start" and "rating_range_end". E.g. 7-8 or 4.5-6.
			Don't return a specific number (e.g. 8.2) unless you're very confident (e.g. this wine has already been rated).
			Also include your reasoning in 2-3 sentences.
			Include your reasoning through the lens of what the experience of the wine would be. Don't use relative ratings. For example, good explaination would be
			"You love rich oaky wines from california with strong tannins." A bad explaination would be "You rank california cabernets around 7.6."

			Here is an Example:

			New Wine: "2016 Kelly Fleming Napa Valley Cabernet Sauvignon (Winery Direct Library Release). A towering, statuesque wine, the 2016 Cabernet Sauvignon Estate is every bit as impressive as it has been on past tastings. In the glass, the 2016 is powerful, dense and explosive, with tremendous energy and sheer power. The dark, muscular intensity of Calistoga comes through loud and clear. (AG) 97+"
			Historical Wine Tasting Data:
			[{{'tasting_id': 118,
			  'notes': None,
			  'tasted_at': datetime.datetime(2009, 8, 28, 4, 17, 25),
			  'unit_price': 13.0,
			  'unit_size': None,
			  'entry_id': 275,
			  'entry_name': None,
			  'rating': 6.0,
			  'alcohol': 13.0,
			  'color': '--- !map:HashWithIndifferentAccess \nblue: "0.000000"\ngreen: "0.015686"\nred: "0.164706"\nalpha: "1.000000"\n',
			  'vintage': 2007,
			  'producer_name': 'Medrano',
			  'region_name': 'Mendoza ',
			  'country_name': 'Argentina',
			  'varieties': 'Malbec',
			  'tags': None}},
			 {{'tasting_id': 69,
			  'notes': 'Birthday dinner with Mo! 29 years old. Very light and tasty.',
			  'tasted_at': datetime.datetime(2009, 8, 22, 2, 56, 12),
			  'unit_price': 55.0,
			  'unit_size': None,
			  'entry_id': 239,
			  'entry_name': 'ZUNI',
			  'rating': 8.3,
			  'alcohol': 13.0,
			  'color': '--- !map:HashWithIndifferentAccess \nblue: "0.203922"\ngreen: "0.000000"\nred: "0.600000"\nalpha: "1.000000"\n',
			  'vintage': 2007,
			  'producer_name': 'Hirsch Vineyards',
			  'region_name': None,
			  'country_name': 'United States',
			  'varieties': 'Pinot Noir',
			  'tags': None}}]]


			 Response (structured as JSON):
			 {{
				"rating_range_start" : 8.1,
				"rating_range_end" : 9.0,
				"reasoning" : "INSERT REASONING HERE USING APPROACHABLE WINE APPRECIATION VOCABULARY. KEEP IT TO 2-3 SENTENCES."
				"structured_input" : {{
					"region" : "Napa Valley",
					"country" : "United States",
					"varietals" : "Cabernet",
					"unit_price" : 0.0,
					"unit_size" : "750ml",
					"drink_with" : "bbq, middle eastern cuisine, chocolate ice cream",
					"price_point" : "2/5"
					"tags" : "smokey, black, jammy",
					etc...
				}}
			 }}
			"""
			},
			{"role": "user", "content": user_message}]
		)
		str_response = response.choices[0].message.content
		print(str_response)		
		return str_response
	except openai.RateLimitError:
		print("Rate limit hit! Waiting before retrying...")
		time.sleep(10)  # Wait before retrying		


def predict_best_wine(wine_options, wine_ratings):
	try:
		wine_data_string = json.dumps(wine_ratings, indent=4, sort_keys=True, default=str)
		wine_options_string = json.dumps(wine_options, indent=4, sort_keys=True, default=str)
		user_message = f"""
			Wines to Choose From: 
			{wine_options_string}

			Historical Tasting Data:
			{wine_data_string}
		"""
		response = openai.chat.completions.create(
			model="o3-mini",
			reasoning_effort="low", #"medium", #"high",
			response_format={ "type": "json_object" },
			messages=[{"role": "system", "content": f"""You are a world famous sommelier, renown for your intuition and predictive powers. 
			I am a wine drinker who lives in San Francisco, California and I wan't you to help me decide on a wine from a list of options.
			You will be provided with my "historical wine tasting data." 
			In this data, the "rating" value is on a 10-point scale.
			You will also be given an list of wines that I have not tasted. Some of these may have ratings in the 100 point scale.			
			Given the tasting data that is provided, I'd like you to choose the one I would like the most. 
			Also include your reasoning in 1-3 sentences.

			Here is an Example:

			Wines to Choose From: 
			[
				"1982 Mouton Rothschild, Pauillac (Pre-Arrival): $1,549.99",
				"2023 Benmar "Alpine Lakes" Dundee Hills Pinot Noir: $75",
				"2023 Benmar "Into the Fog" Willamette Valley Pinot Noir: $45",
				"Ragnaud-Sabourin "Fontvieille #35" K&L Exclusive Cognac (750ml): $179.99",
				"2023 Domaine Paul Pernot Côte d'Or Bourgogne Blanc: $29.99",
				"2023 Benmar "Sand Dune" Dundee Hills Chardonnay: $55",
				"2016 Tronquoy-Lalande, St-Estèphe: $36.95",
				"2020 Château Gigognan Côtes-du-Rhône Villages Signargues: $14.99",
				"2010 Haut-Brion, Pessac-Léognan (Pre-Arrival): $849.00" 
			]

			Historical Wine Tasting Data:
			[{{'tasting_id': 118,
			  'notes': None,
			  'tasted_at': datetime.datetime(2009, 8, 28, 4, 17, 25),
			  'unit_price': 13.0,
			  'unit_size': None,
			  'entry_id': 275,
			  'entry_name': None,
			  'rating': 6.0,
			  'alcohol': 13.0,
			  'color': '--- !map:HashWithIndifferentAccess \nblue: "0.000000"\ngreen: "0.015686"\nred: "0.164706"\nalpha: "1.000000"\n',
			  'vintage': 2007,
			  'producer_name': 'Medrano',
			  'region_name': 'Mendoza ',
			  'country_name': 'Argentina',
			  'varieties': 'Malbec',
			  'tags': None}},
			 {{'tasting_id': 69,
			  'notes': 'Birthday dinner with Mo! 29 years old. Very light and tasty.',
			  'tasted_at': datetime.datetime(2009, 8, 22, 2, 56, 12),
			  'unit_price': 55.0,
			  'unit_size': None,
			  'entry_id': 239,
			  'entry_name': 'ZUNI',
			  'rating': 8.3,
			  'alcohol': 13.0,
			  'color': '--- !map:HashWithIndifferentAccess \nblue: "0.203922"\ngreen: "0.000000"\nred: "0.600000"\nalpha: "1.000000"\n',
			  'vintage': 2007,
			  'producer_name': 'Hirsch Vineyards',
			  'region_name': None,
			  'country_name': 'United States',
			  'varieties': 'Pinot Noir',
			  'tags': None}}]]


			 Response (structured as JSON):
			 {{
				"top_pick" : "2023 Benmar "Into the Fog" Willamette Valley Pinot Noir",
				"reasoning" : "INSERT REASONING HERE USING APPROACHABLE WINE APPRECIATION VOCABULARY. KEEP IT TO 1-3 SENTENCES."
				"structured_input" : {{
					"region" : "Willamette Valley",
					"country" : "United States",
					"varietals" : "Pinot Noir",
					"unit_price" : $45,
					"unit_size" : "750ml",
					"drink_with" : "pheasant, tea cakes, almonds",
					"price_point" : "Moderate"
					"tags" : "light, fruity, floral",
					etc...
				}}
			 }}
			"""
			},
			{"role": "user", "content": user_message}]
		)
		str_response = response.choices[0].message.content
		print(str_response)		
		return str_response
	except openai.RateLimitError:
		print("Rate limit hit! Waiting before retrying...")
		time.sleep(10)  # Wait before retrying		

def recommend_wine_for_occasion(occasion, wine_ratings):
	try:
		wine_data_string = json.dumps(wine_ratings, indent=4, sort_keys=True, default=str)
		user_message = f"""
			Occasion to match: "{occasion}"

			Historical Tasting Data:
			{wine_data_string}
		"""
		response = openai.chat.completions.create(
			model="o3-mini",
			reasoning_effort="low", #"medium", #"high",
			response_format={ "type": "json_object" },
			messages=[{"role": "system", "content": f"""You are a world famous sommelier, renown for your intuition and predictive powers. 
			I am a wine drinker who lives in San Francisco, California and I wan't you to recommend a wine that suits a occasion/setting/category.
			You will be provided with my "historical wine tasting data." 
			In this data, the "rating" value is on a 10-point scale.
			Based on the tasting data that is provided, I'd like you to recommend a new wine that I have not tasted, but fits my preferences.
			You can select the wine from your own knowledge based, but do not select on from the list I've provided.
			Vintages can be skipped, or be a range, or be a specific year.
			Also include your reasoning in 2-3 sentences. Explain why this wine is interesting and what I might smell, taste, and think about when drinking. Be as specific as possible.

			Here is an Example:

			Occasion to match: "Friday night movie at home"

			Historical Wine Tasting Data:
			[{{'tasting_id': 118,
			  'notes': None,
			  'tasted_at': datetime.datetime(2009, 8, 28, 4, 17, 25),
			  'unit_price': 13.0,
			  'unit_size': None,
			  'entry_id': 275,
			  'entry_name': None,
			  'rating': 6.0,
			  'alcohol': 13.0,
			  'color': '--- !map:HashWithIndifferentAccess \nblue: "0.000000"\ngreen: "0.015686"\nred: "0.164706"\nalpha: "1.000000"\n',
			  'vintage': 2007,
			  'producer_name': 'Medrano',
			  'region_name': 'Mendoza ',
			  'country_name': 'Argentina',
			  'varieties': 'Malbec',
			  'tags': None}},
			 {{'tasting_id': 69,
			  'notes': 'Birthday dinner with Mo! 29 years old. Very light and tasty.',
			  'tasted_at': datetime.datetime(2009, 8, 22, 2, 56, 12),
			  'unit_price': 55.0,
			  'unit_size': None,
			  'entry_id': 239,
			  'entry_name': 'ZUNI',
			  'rating': 8.3,
			  'alcohol': 13.0,
			  'color': '--- !map:HashWithIndifferentAccess \nblue: "0.203922"\ngreen: "0.000000"\nred: "0.600000"\nalpha: "1.000000"\n',
			  'vintage': 2007,
			  'producer_name': 'Hirsch Vineyards',
			  'region_name': None,
			  'country_name': 'United States',
			  'varieties': 'Pinot Noir',
			  'tags': None}}]]

			 Response (structured as JSON):
			 {{
			 	"category" : "occasion",
			 	"title" : <A SHORT TITLE FOR THE RESPONSE. E.g. 39th BIRTHDAY GIFT>,
				"query" : "Friday night movie at home",
			 	"analysis" : {{
					"top_pick" : "2023 Husch Anderson Valley Pinot Noir",
					"structured_input" : {{
						"region" : "Anderson Valley, California",
						"country" : "United States",
						"varietals" : "Pinot Noir",
						"unit_price" : $25,
						"unit_size" : "750ml",
						"drink_with" : "popcorn, sriracha, pork",
						"price_point" : "Affordable"
						"tags" : "light, fruity, floral",
						etc...
					}}
			 	}}
				"reasoning" : <INSERT REASONING HERE USING APPROACHABLE WINE APPRECIATION VOCABULARY. KEEP IT TO 1-3 SENTENCES.>
			 }}
			"""
			},
			{"role": "user", "content": user_message}]
		)
		str_response = response.choices[0].message.content
		json_response = json.loads(str_response)
		wine_descr = json_response['analysis']['top_pick']
		buy_link = get_buy_link(wine_descr)
		json_response['analysis']['buy_link'] = buy_link
		str_response = json.dumps(json_response)
		print(str_response)		
		return str_response
	except openai.RateLimitError:
		print("Rate limit hit! Waiting before retrying...")
		time.sleep(10)  # Wait before retrying		


os.environ["TOKENIZERS_PARALLELISM"] = "false"

structured_wines = []

SQL_LIMIT = 1000

# Database connection URL
# username = 'default'
# password = 'Default'
# host = 'localhost'
# database = 'Wine_Note'
# db_url = f'mysql+pymysql://{username}:{password}@{host}/{database}'


# Create an SQLAlchemy engine for MySQL
engine = create_engine("mysql+pymysql://root:@localhost:3306/winenotes_production")
#engine = create_engine(db_url)

# Wrap the connection with LlamaIndex's SQLDatabase
sql_database = SQLDatabase(engine)

query_engine = NLSQLTableQueryEngine(
	sql_database=sql_database, tables=["common_countries", "common_entries", "common_locations", "common_producers", 
	"common_regions", "common_tag_pointers", "common_tags", "common_varieties", "common_variety_pointers", 
	"countries", "entries", "entries_tags", "entries_varieties", "locations", "metrics", "producers",  "regions", 
	"tags", "tastings", "users", "varieties"], 
	# llm=llm
)

# EXAMPLE
# Get all of bill's tastings
user_select = "WHERE u.id = 2"

query = f"""
SELECT 
	t.id AS tasting_id,
	t.notes,
	t.tasted_at,
	t.unit_price,
	t.unit_size,
	e.id AS entry_id,
	e.name AS entry_name,
	e.rating,
	e.alcohol,
	e.color,
	e.vintage,
	p.name AS producer_name,
	r.name AS region_name,
	c.name AS country_name,
	GROUP_CONCAT(DISTINCT v.name ORDER BY v.name SEPARATOR ', ') AS varieties,
	GROUP_CONCAT(DISTINCT tg.name ORDER BY tg.name SEPARATOR ', ') AS tags
FROM tastings t
JOIN entries e ON t.entry_id = e.id
JOIN users u ON e.user_id = u.id
LEFT JOIN producers p ON e.producer_id = p.id
LEFT JOIN regions r ON e.region_id = r.id
LEFT JOIN countries c ON e.country_id = c.id
LEFT JOIN entries_varieties ev ON e.id = ev.entry_id
LEFT JOIN varieties v ON ev.variety_id = v.id
LEFT JOIN entries_tags et ON e.id = et.entry_id
LEFT JOIN tags tg ON et.tag_id = tg.id
{user_select}
GROUP BY t.id, e.id, p.name, r.name, c.name
ORDER BY t.tasted_at DESC
LIMIT {SQL_LIMIT};
"""

# Execute query
result = query_engine.query(query)
# print(result)
# E.g.
# Based on the query results, here are some wine tasting notes:

# 1. A Cabernet Sauvignon from Arrington Vineyards, United States, with little info on-label. Purchased in Tennessee and drank as a toast on the weekend of Grandma Lindmeier's funeral.
# 2. A Pinot Noir from Inman, Russian River Valley, with a rating of 8.4 and vintage 2006.
# 3. A Viognier from Arrington Vineyards, Tennessee, with a rating of 7.9 and vintage 2004.
# 4. A Barolo from Amber Knolls Vineyard, with tasting notes of ash, bacon, black pepper, brown sugar, butter, cashew, and cedar.
# 5. A blend of Carignane, Mataro, Petit Syrah, and Zinfandel from Ridge, California, with a vintage of 2008.

# These are just a few examples of the wine tasting notes extracted from the query results.

#TODO 1: Feed all of these into an OpenAI context and ask to summarize my taste.

# Wine Taster Profile:

# Our SF‐based wine enthusiast is a discerning but unpretentious taster who clearly gravities toward robust, 
# well‐made reds with personality and nuance. He consistently awards high marks (8.0 and above) to expressive 
# Californian wines—a range of Napa and Sonoma Cabernets, well‐crafted Zinfandels (like Ridge’s “Geyserville” 
# 	and “Lytton Springs”), and elegant Pinot Noirs from regions such as the Russian River and Mendocino. 
# He’s not afraid to venture beyond his backyard, however, as evidenced by his high ratings for Italian 
# Barolos (one from Amber Knolls scoring 8.7, for example), where he praises layers of savory notes like ash, 
# bacon, black pepper, brown sugar, butter, cashew, and cedar.

# His tasting notes reveal a playful yet meticulous palate. He’s quick to comment on both immediate impressions 
# (“not a huge fan of the opening smell, but nice, jammy flavor”) and evolving characteristics as the wine breathes, 
# and isn’t shy about humorous quips—even noting when a wine “tastes like poop” in a tongue‐in‐cheek way. This blend 
# of technical observation and situational commentary (wines savored during family gatherings, celebratory dinners, 
# 	or even a bittersweet toast at a funeral) paints a picture of someone who values both the quality and the story 
# behind a wine.

# Geographically, his experience is steeped in local terroir—many tastings occur at or near iconic SF locales like 
# Faletti’s—with a clear bias for California’s diversity (from Napa and Sonoma to Alexander Valley and Calistoga). 
# He does sample international wines (from France, Italy, Australia, Argentina, and Chile), but his highest praises 
# and strongest connections lie with the bold, fruit‐driven, structured reds of his own region. He also keeps an eye 
# on price and provenance, readily noting when a wine offers exceptional value (“Godd wine for the price”) or when 
# its backstory enhances the tasting experience.

# When imagining his next review, expect a wine that unfolds on the nose with layers of ripe dark fruit, a dash of 
# spice (black pepper or subtle oak‐derived cedar), and a balanced acidity that carries through to a lingering finish. 
# He’ll likely reward wines that marry plush fruit with refined, integrated tannins—wines that tell a story and 
# elevate life’s memorable moments.

# For the sommelier: Recommend a wine with complexity and warmth—a structured Napa Cabernet blend or a nuanced 
# Sonoma red that delivers both immediate aromatic intrigue and evolving layers of dark fruit and spice. This choice 
# should appeal to his taste for wines that are both rooted in Californian terroir and rich in character, comfortable 
# enough for a celebratory family gathering yet sophisticated in its profile.

tastings = result.source_nodes[0].metadata['result']
print(f"Found {len(tastings)} tastings")
column_names = result.source_nodes[0].metadata['col_keys']
structured_wines = [dict(zip(column_names, row)) for row in tastings]

# print("Reasoning...")

openai_client = OpenAI()

# summary = summarize_my_prefs(structured_wines)

#TODO 2: Put the data into the system prompt and pass in new wines to estimate a rating.
# {
#   "rating": 8.0,
#   "reasoning": "Based on your historical preferences, you tend to enjoy well-made wines with a balanced complexity and structure. Although many of your highly rated entries are from the United States, the 2016 Tronquoy-Lalande from St-Estèphe is a Bordeaux with a refined profile and a moderate price, which should appeal to your palate and yield an approximately 8.0 rating.",
#   "structured_input": {
#     "region": "St-Estèphe",
#     "country": "France",
#     "varietals": "Bordeaux Blend",
#     "price": "$36.99",
#     "vintage": 2016,
#     "drink_with": "red meats, robust stews, aged cheeses",
#     "price_point": "Moderate",
#     "tags": "structured, elegant, balanced"
#   }
# }

# prediction = predict_wine_rating("2016 Tronquoy-Lalande, St-Estèphe Price: $36.99", structured_wines)
# prediction = predict_wine_rating("chateau aney haut-medoc bordeaux", structured_wines) # Predicted 6.5-7.5, I gave it a 7.5
# prediction = predict_wine_rating("thevenet & fils burgundy pinot noir", structured_wines)

# TODO 3: Pick from a list

# list_prediction = predict_best_wine([	
# 					"1982 Mouton Rothschild, Pauillac (Pre-Arrival): $1,549.99",
# 					"2023 Benmar \"Alpine Lakes\" Dundee Hills Pinot Noir: $75",
# 					"2023 Benmar \"Into the Fog\" Willamette Valley Pinot Noir: $45",
# 					"Ragnaud-Sabourin \"Fontvieille #35\" K&L Exclusive Cognac (750ml): $179.99",
# 					"2023 Domaine Paul Pernot Côte d'Or Bourgogne Blanc: $29.99",
# 					"2023 Benmar \"Sand Dune\" Dundee Hills Chardonnay: $55",
# 					"2016 Tronquoy-Lalande, St-Estèphe: $36.95",
# 					"2020 Château Gigognan Côtes-du-Rhône Villages Signargues: $14.99",
# 					"2010 Haut-Brion, Pessac-Léognan (Pre-Arrival): $849.00"
# 					], structured_wines)

# TODO 4: Recommend for a category

# recommend_wine_for_occasion("Friday night movie at home", structured_wines)
# recommend_wine_for_occasion("39th birthday gift for co-worker", structured_wines)
#recommend_wine_for_occasion("A Brit visiting Cupertino, CA looking for an affordable example of the local wines", structured_wines)
# recommend_wine_for_occasion("Cheep wines that taste expensive", structured_wines)


# recommend_wine_for_occasion("My platonic ideal wine", structured_wines)

# TODO 5: Select best wine from image
# Dont do this. Slow
## menu_wines = load_wines_from_image("./menu_full.jpeg")
## prediction = predict_best_wine(menu_wines, structured_wines)

# Do this
# select_best_wine_from_image("./menu_full.jpeg", structured_wines)

# general_image_upload_image("./menu_full.jpeg", structured_wines)
# general_image_upload_image("./menu_reds.jpeg", structured_wines)
# general_image_upload_image("./wine_label.jpeg", structured_wines)
# general_image_upload_image("./food.jpeg", structured_wines)