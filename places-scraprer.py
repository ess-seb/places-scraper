from bs4 import BeautifulSoup as bs #pip install beautifulsoup4
import urllib.request
import json
import re
import codecs

########################
#                      #
#    CONTROL PANEL     #
#                      #
########################


apiQuery = "biuro"
apiRadious = 50000
apiType = "travel_agency"
apiKey = "AIzaSyCYxSVDHCuB1YNR-ZvALA3dlfUYpMuLTsw"
apiLanguage = "pl"
apiSensor = "false"
apiLocation = "50.26265849772663,19.02935028076172"

contWords = "|".join(["kontakt", "Kontakt", "Contact", "contact", "KONTAKT", "CONTACT"])
myFile = codecs.open('mojcion.json', 'a', 'utf-8')

#########################

status = ""
# urlFirst = "https://maps.googleapis.com/maps/api/place/textsearch/json?types=%s&location=%s&radius=50000&language=%s&query=%s&sensor=%s&key=%s" % (apiType, apiLocation, apiLanguage, apiQuery, apiSensor, apiKey)
urlFirst = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=%s&types=%s&rankby=distance&key=%s" % (apiLocation, apiType, apiKey)
# urlNext = "https://maps.googleapis.com/maps/api/place/textsearch/json?pagetoken=%s&sensor=%s&key=%s"
urlNext = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?pagetoken=%s&key=%s"
nextPageToken = ""
data = []
pageDict = {}  # strona wyników wyszukiwania
pageNo = 0
gRequests = 0
grLimit = 1000



def readPage(url):  # zwraca (listę, słowników) stronę odpowiedzi z palces
    # print(url)
    pageJson = urllib.request.urlopen(url).read()
    #print(pageJson)
    # print(url)
    readPageDict = json.loads(pageJson.decode("utf-8"))  # json->str->dict
    global status
    global gRequests
    global nextPageToken
    status = readPageDict['status']
    resultKeys = readPageDict.keys()

    gRequests += 1
    if "results" in resultKeys:
        nextPageToken = readPageDict.get("next_page_token", None)
        print("\nnew Next Page Token: %s\n" % nextPageToken)
        return readPageDict["results"]
    elif "result" in resultKeys:
        return readPageDict["result"]
    else:
        print("Eroor: there is no \'result\' nor \'results\' key")
        return {}


def getPlace(placeReference):  # zwraca słownik, szegóły miejsca, pobiera kode refernece do konkretnego miejsca
    #urllib.urlencode({
    #    'reference': placeReference
    #})
    urlPlaceDetailsPage = "https://maps.googleapis.com/maps/api/place/details/json?reference=" + placeReference + "&key=" + apiKey
    detailsDict = readPage(urlPlaceDetailsPage)
    return detailsDict


def findContactLink(url):
    # print(url)
    if url[len(url) - 1] == '/':
        url = url[:-1]
    links = []
    linksNoDup = []
    try:
        web = bs(urllib.request.urlopen(url).read())
        contactLinkS = web.find('body').findAll('a')
        for contactLink in contactLinkS:
            if re.search(contWords, contactLink.text):
                newLink = contactLink["href"]
                if ("http" in newLink) | ("www" in newLink):
                    links.append(newLink)
                else:
                    if newLink[0] == '/':
                        newLink = newLink[1:]
                    links.append(url + "/" + newLink)
        linksNoDup = list(set(links))
    except Exception as e:
        linksNoDup.append(str(e))
        print("Company page ERROR: %s" % url)
    finally:
        return linksNoDup


def findEmails(whereUrl):
    emailsNoDup = []
    try:
        webString = urllib.request.urlopen(whereUrl).read()
        emails = re.findall(r"[0-9.\-_a-zA-Z]+@[0-9.\-_a-zA-Z]+\.[-_.0-9a-zA-Z]{2,6}|[0-9.\-_a-zA-Z]+\[at\][0-9.\-_a-zA-Z]+\.[-_.0-9a-zA-Z]{2,6}", webString.decode("utf-8"))
        emailsNoDup = list(set(emails))
    except Exception as e:
        emailsNoDup.append(str(e))
        print("Contact page ERROR: %s" % whereUrl)
    finally:
        return emailsNoDup


def agregatePlace(place, contactLinks, emails):
    dataPlace = {}
    addressCompo = {}

    for e in place['address_components']:
        for t in e['types']:
            addressCompo[t] = e['long_name']

    dataPlace = {
            "name": place["name"],
            "formatted_phone_number": place["formatted_phone_number"],
            "international_phone_number": place["international_phone_number"],
            "website": place["website"],
            "contact_page": contactLinks,
            "emails": emails,
            # "rating": place["rating"],
            "location": {
               "lat": place["geometry"]["location"]["lat"],
               "lng": place["geometry"]["location"]["lng"]
            },
            "formatted_address": place["formatted_address"],
            "address_components": {
                "street_number": addressCompo.get("street_number", None),
                "route": addressCompo.get("route", None),
                "city": addressCompo.get("locality", None),
                "state": addressCompo.get("administrative_area_level_1", None),
                "country": addressCompo.get("country", None),
                "postal_code": addressCompo.get("postal_code", None)
            }
        }
    return dataPlace


def saveData(toSave):
    print("Saving... I hope...")
    for rowSave in toSave:
        myFile.write(json.dumps(rowSave) + ",\n")


def newApiKey():
    global apiKey
    global grLimit
    apiKey = raw_input("Input new Google Places Api Key")
    grLimit = int(raw_input("Input requests limit for the Key"))


print("Lokalizacja:")
loc = raw_input()
if lok != "": apiLocation = lok

url = urlFirst
while True:
    pageSearch = readPage(url)
    if status != "OK":
        saveData(data)
        print("Status Google Places NOT OK")
        break

    if gRequests > 998:
        newApiKey()

    for searchRecord in pageSearch:
        place = getPlace(searchRecord["reference"])
        if place.get("website"):
            links = findContactLink(place.get("website", []))
        else:
            place["website"] = []
            links = []

        emails = []
        for link in links:
            emails = findEmails(link)

        thisData = agregatePlace(place, links, emails)
        print('%70s  |    emails: %3s    |     requests: %3s    |    page: %3s    |    status %3s' % (thisData["name"], len(thisData["emails"]), gRequests, pageNo, status))
        data.append(thisData)
        # print data

    saveData(data)
    data = []

    if not nextPageToken:
        print("Warning: No next_page_token status: %s" % status)
        break
    url = urlNext % (nextPageToken, apiKey)
    pageNo += 1

    # if pageNo == 3:
    #     break


def save_csv(data, file_path=""):
    pigi_list = []
    new_file = True
    root = Tk()
    root.withdraw()

    if file_path == "":
        file_path = filedialog.asksavefilename(
            title="Zapisz raport z odejmowania PIGI",
            filetypes=[("Wszystkie pliki", ".*"), ("CSV", ".csv")],
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





# i = 0

# while pageSearch['next_page_token']:
#     i += 1 
#     if i == 2: 
#         exit(0)

#     urlNext = "https://maps.googleapis.com/maps/api/place/textsearch/json?pagetoken="+pageSearch['next_page_token']+"&sensor="+apiSensor+"&key="+apiKey
#     pageSearch = readPage(urlNext)
#     doPlaces(pageSearch)



##########################################

# # urlN = pageSearch['']
# # $print json.dumps({'apple': 'cat', 'banana':'dog', 'pear':'fish'}) #dict->jsonStr

# txt = raw_input('Pytam się ciebie')

# text = " <a href=\"/kbontakt\">SKontaktować</a>"
# if re.search("|".join(contWords), text): print "yo"

    # if s.endswith(" "): s = s[:-1]
     # if s.startswith(" "): s = s[1:]


# "bla bla bla %20s bla bla %s" % ("yo yo yo", "wtf") #ile ma zarezerwować miejsca na placeholder

# for imie, rola in zip(["janek", "edek", "maciej"], ["przyjaciel", "brat", "kuzyn"])
#    print "text %s ty %s" % (imie, rola)
# %.2f (float dwa miejsce po przecinku)

#lista = [1, 2, 3]
#kwadraty = [e **2 for e in lista]
# kwadraty = [e: e **2 for e in lista]
# kwadraty = [e: * 2 for e in lista if e>2]
# kwadraty = [e for row in lista for e in row if e > 2]


#for licznik, wynik in enumerate(wyniki_dane, 1) # 1 znaczy żeby numerował od 1

# a, b, c = ['a', 'b', 'c']
# if lista.isdigit():
# print "Tomek, Bartek, Jurek, Alicja".rsplit(",", 1)  #1-podzil raz split() od lewej rsplit od prawej
