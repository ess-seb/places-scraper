from bs4 import BeautifulSoup as bs #pip install beautifulsoup4
import urllib.request
import json
import re
import codecs


api_radious = 0
api_type = ""
api_key = ""
location = ""
cont_words = ""
status = ""
url_first = 'https://maps.googleapis.com/maps/api/place/'\
            'nearbysearch/json?location=%s&types=%s&rankby=distance&key=%s'
url_next = 'https://maps.googleapis.com/maps/api/place/'\
           'nearbysearch/json?pagetoken=%s&key=%s'
url_place_details = 'https://maps.googleapis.com/maps/api/place/'\
                    'details/json?reference=%s&key=%s'
next_page_token = ""
data = []
page_dict = {} 
page_no = 1
g_requests = 0
gr_limit = 1000


def get_search_page(url):
    page_json = urllib.request.urlopen(url).read()
    search_page = json.loads(page_json.decode("utf-8"))  # json->bit->str->dict
    if search_page['status'] != "OK":
        print("Error: %s" % search_page['status'])
        raise("Error: API Status is NOT OK")
    return search_page


def get_place(place_refference, url_place_details, api_key):
    url_place_details = url_place_details  % (place_refference, api_key)
    details_dict = get_search_page(url_place_details).get("result", {})
    return details_dict


def find_contact_links(url):
    # print(url)
    if url[len(url) - 1] == '/':
        url = url[:-1]
    links = []
    try:
        web = bs(urllib.request.urlopen(url).read())
        contact_link_s = web.find('body').findAll('a')
        for contact_link in contact_link_s:
            if re.search(cont_words, contact_link.text):
                new_link = contact_link["href"]
                if ("http" in new_link) | ("www" in new_link):
                    links.append(new_link)
                else:
                    if new_link[0] == '/':
                        new_link = new_link[1:]
                    links.append(url + "/" + new_link)
        links = list(set(links))
    except Exception as er:
        links.append(str(er))
        print("Place page ERROR: %s" % url)
    finally:
        return links


def find_emails(where_url):
    emails = []
    try:
        web_string = urllib.request.urlopen(where_url).read()
        emails = re.findall(r'[0-9.\-_a-zA-Z]+@'\
                            '[0-9.\-_a-zA-Z]+\.[-_.0-9a-zA-Z]{2,6}|'\
                            '[0-9.\-_a-zA-Z]+\[at\][0-9.\-_a-zA-Z]+\.'\
                            '[-_.0-9a-zA-Z]{2,6}', web_string.decode("utf-8"))
        emails = list(set(emails))
    except Exception as er:
        emails.append(str(er))
        print("Email page ERROR: %s" % where_url)
    finally:
        return emails


def agregate_place(place, contact_link_s, emails):
    data_place = {}
    address_compo = {}

    for e in place['address_components']:
        for t in e['types']:
            address_compo[t] = e['long_name']

    data_place = {
            "name": place.get("name", None),
            "formatted_phone_number": place.get("formatted_phone_number", None),
            "international_phone_number": place.get("international_phone_number", None),
            "website": place.get("website", None),
            "contact_page": contact_link_s,
            "emails": emails,
            "lat": place["geometry"]["location"]["lat"],
            "lng": place["geometry"]["location"]["lng"],
            "formatted_address": place.get("formatted_address", None),
            "address_components": {
                "street_number": address_compo.get("street_number", None),
                "route": address_compo.get("route", None),
                "city": address_compo.get("locality", None),
                "state": address_compo.get("administrative_area_level_1", None),
                "country": address_compo.get("country", None),
                "postal_code": address_compo.get("postal_code", None)
            }
        }
    return data_place


def save_data(data):
    my_file = codecs.open('output.json', 'w', 'utf-8')
    print("Saving... I hope... output.json")
    # for row_data in data:
    #     my_file.write(json.dumps(row_data) + ",\n")
    my_file.write(json.dumps(data))


def load_config():
    json_file=codecs.open('config.json', 'r', 'utf-8')
    json_config = json.load(json_file)
    json_file.close()
    return json_config




json_config = load_config()
api_radious = json_config.get("search_radious")
api_type = json_config.get("place_type")
api_key = json_config.get("api_key")
cont_words = "|".join(json_config.get("where_emails"))

loc_r = re.compile('\d+\.*\d*,\d+\.*\d*')

while True:
    print("Location: i.e.: 50.262,19.029")
    loc = input()
    if (loc_r.match(loc) is not None) | (loc == ""): break
    else: print("Error: wrong format take a look at the example")

location = loc if loc != "" else json_config.get("default_location") 
url = url_first % (location, api_type, api_key)

try:
    while True: #while-do
        print(url)
        search_page = get_search_page(url)
        next_page_token = search_page.get("next_page_token", None)
        # print("\nnew Next Page Token: %s\n" % next_page_token)
        places_page = search_page.get("results", {})
        
        g_requests += 1
        if g_requests > 998:
            api_key = input("Input a new Google Places Api Key")
            gr_limit = int(input("Input requests limit for the Key"))
            g_requests = 0

        for search_record in places_page:
            place = get_place(search_record["reference"], url_place_details, api_key)
            if place.get("website"):
                links = find_contact_links(place.get("website", []))
            else:
                place["website"] = []
                links = []

            emails = []
            for link in links:
                emails = find_emails(link)

            this_data = agregate_place(place, links, emails)
            print('%s \nemails: %3s  |  API page: %3s\n\n'
                  % (this_data["name"], len(this_data["emails"]), page_no))
            data.append(this_data)
            # print data

        if not next_page_token:
            print("Warning: No next_page_token status")
            break

        url = url_next % (next_page_token, api_key)
        page_no += 1

except Exception as e:
    print(e)
    # raise

finally:
    save_data(data)
    pass