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
page_no = 0
g_requests = 0
gr_limit = 1000


def read_page(url):
    page_json = urllib.request.urlopen(url).read()
    read_page_dict = json.loads(page_json.decode("utf-8"))  # json->bit->str->dict
    if read_page_dict['status'] != "OK": raise("API Status is NOT OK")

    resultKeys = read_page_dict.keys()
    if "results" in resultKeys:
        next_page_token = read_page_dict.get("next_page_token", None)  // NIIIIIIIIIIIIIIIIIIIIIIIE JEST PRZEKAZYWANY
        print("\nnew Next Page Token: %s\n" % next_page_token)
        return read_page_dict["results"]
    elif "result" in resultKeys:
        return read_page_dict["result"]
    else:
        print("Eroor: there is no \'result\' nor \'results\' key")
        return {}


def get_place(place_refference, url_place_details, api_key):s
    details_dict = read_page(url_place_details % (place_refference, api_key))
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
            "name": place["name"],
            "formatted_phone_number": place["formatted_phone_number"],
            "international_phone_number": place["international_phone_number"],
            "website": place["website"],
            "contact_page": contact_link_s,
            "emails": emails,
            # "rating": place["rating"],
            "location": {
               "lat": place["geometry"]["location"]["lat"],
               "lng": place["geometry"]["location"]["lng"]
            },
            "formatted_address": place["formatted_address"],
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


def save_data(toSave):
    my_file = codecs.open('mojcion.json', 'a', 'utf-8')
    print("Saving... I hope...")
    for rowSave in toSave:
        my_file.write(json.dumps(rowSave) + ",\n")


def load_config():
    json_file=codecs.open('config.json', 'r', 'utf-8')
    json_config = json.load(json_file)
    json_file.close()
    return json_config


def save_csv(data, file_path=""):
    pigi_list = []
    new_file = True
    root = Tk()
    root.withdraw()

    if file_path == "":
        file_path = filedialog.asksavefilename(
            title="Save CSV",
            filetypes=[("All files", ".*"), ("CSV", ".csv")],
            parent=root)

    if not ".csv" in file_path:
        file_path += ".csv"

    new_file = not os.path.isfile(file_path)

    try:
        my_file = open(file_path, 'a')

        if new_file:
        # jeśli plik jest nowy dodaje klucze jako wiersz z etykietami
            row = ";".join([keys for keys in data[0]])
            row += "\n"
            my_file.writelines(row)

        for datarow in data:
            row = ";".join([str(datarow[cell]) for cell in datarow])
            row = row.replace(".", ",")
            row += "\n"
            my_file.writelines(row)

        my_file.close()
        print("RAPORT has been saved: %s" % file_path)
        return file_path

    except Exception as e:
        print("ERROR: raport has been NOT saved because of %s" % str(e))
        return False





json_config = load_config()
api_radious = json_config.get("search_radious")
api_type = json_config.get("place_type")
api_key = json_config.get("api_key")
cont_words = "|".join(json_config.get("where_emails"))

print("Location: i.e.: 50.262,19.029")
loc = input()
location = loc if loc != "" else json_config.get("default_location") 

url = url_first % (location, api_type, api_key)
while True:
    print(url)
    page_search = read_page(url)
    g_requests += 1
    if g_requests > 998:
        api_key = input("Input a new Google Places Api Key")
        gr_limit = int(input("Input requests limit for the Key"))
        g_requests = 0

    for search_record in page_search:
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
        print('%70s  |    emails: %3s    |     requests: %3s    |    page: %3s    |    status %3s' % (this_data["name"], len(this_data["emails"]), g_requests, page_no, status))
        data.append(this_data)
        # print data

    save_data(data)
    data = []

    if not next_page_token:
        print("Warning: No next_page_token status: %s" % status)
        break
    url = url_next % (next_page_token, api_key)
    page_no += 1
