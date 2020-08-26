# import urllib.request as urllib2
import struct
import io
import requests
from bs4 import BeautifulSoup
import azureKey
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from textPredictors import TextPredicor
import numpy as np
from PIL import Image ,ImageFile
import urllib
import time

# the reason I'm using  '|' in my urls instead of '/' is because i want to pass
# my url within the api request url... That's why i need to do preprocessing
# The chrome extension will convert the url to use '|' before an API call


class WebProcessor:

    def getUrlData(self, urlString):
        initTime = time.time()
        textPredictor = TextPredicor()
        azureClient = self.authenticate_client()
        print("Time slot 1 : {}".format(time.time() - initTime))


        initTime = time.time()
        url = self._cleanUrl(urlString)
        mainUrlSoup = self._getSoup(url, timeOut=7)
        try:  # jank sollution to checking if there was an error
            if mainUrlSoup == "error":
                return {"error" : "Error in fetching data"}
        except:
            pass
        print("Time slot 2 : {}".format(time.time() - initTime))


        mainUrlData = self._getData(mainUrlSoup)
        mainHeadline = mainUrlData.get("headline")
        mainText = mainUrlData.get("text")
        mainNewsProvider = self.getNewsProvider(urlString)
        initTime = time.time()
        mainImage = self.getImage(mainUrlSoup)
        print("Time slot 3 : {}".format(time.time() - initTime))
        initTime = time.time()

        readingScores = textPredictor.getTextResults(mainText)
        mainReadability = readingScores.get("readability")
        mainReadingTime = readingScores.get("readTime")
        mainSentiment = self._getSentiment(
            azureClient, self.trimAzure(mainText))

        print("Time slot 4 : {}".format(time.time() - initTime))
        #get other relevant news articles 
        initTime = time.time()

        cleanedUrl = url.partition("://")[-1]
        relatedNewsUrls = self._google(mainHeadline)

        print("Time slot 5 : {}".format(time.time() - initTime))
        if cleanedUrl in relatedNewsUrls:
            print("len before remove: ", len(relatedNewsUrls))
            relatedNewsUrls.remove(cleanedUrl)
            print("len after remove: ", len(relatedNewsUrls))
        initTime = time.time()

        relatedNews = []
        for rurl in relatedNewsUrls:
            soup = self._getSoup("https://"+rurl)
            if soup != "error":
                data = self._getData(soup)
                headline = data.get("headline").strip()
                text = data.get("text")
                if len(text) != 0 and len(headline) != 0:
                    readingscore = textPredictor.getTextResults(text)
                    readability = readingscore.get("readability")
                    readingTime = readingscore.get("readTime")
                    newsProvider = self.getNewsProvider(rurl)
                    image = self.getImage(soup)
                    sentiment = self._getSentiment(
                        azureClient, self.trimAzure(text))
                    relatedNews.append({
                        "url": rurl,
                        "newsProvider": newsProvider,
                        "headline": headline,
                        "image": image,
                        # "text": text,
                        "readability": readability,
                        "readingTime": readingTime,
                        "sentiment": sentiment
                    })
                    if len(relatedNews) >= 5:
                        break
        # print("legnth of related news is {}".format(len(relatedNews)))

        print("Time slot 6 : {}".format(time.time() - initTime))
        rating, orderedNews = self._getRating(
            relatedNews, mainReadability, mainReadingTime, mainSentiment)

        toReturn = {
            "headline": mainHeadline,
            # "maintext": mainText,
            "relatedNews": orderedNews,
            "sentiment": mainSentiment,
            "readingTime": mainReadingTime,
            "readability": mainReadability,
            "newsProvider": mainNewsProvider,
            "image": mainImage,
            "rating": rating,
            "error": "none",
        }
        return toReturn

    def _cleanUrl(self, dirtyUrl):
        urlClean = dirtyUrl.replace("|", "/")
        return urlClean

    def _getData(self, soup):
        headline = soup.find_all('h1')
        toRet = "No Headline Found"

        for hl in headline:
            hlText = hl.text
            if len(hlText.split()) >= 4:
                toRet = hlText
                break
        # headline = headline[0].text if len(headline) != 0 else "No Headline"

        text = self.getText(soup)

        return {
            "headline": toRet,
            "text": text,
        }

    def _getSoup(self, url, timeOut = 5):
        page = requests.get(url, timeout = timeOut)
        if page.status_code != 200:
            toRet = "error"
            return toRet

        soup = BeautifulSoup(page.content, 'html.parser')
        return soup

    def _google(self, query):
        googleUrl = "https://www.google.com/search?client=ubuntu&channel=fs&q=" + \
            query + "&ie=utf-8&oe=utf-8"
        results = requests.get(googleUrl)
        googleSoup = BeautifulSoup(results.content, 'html.parser')
        urlResults = []

        #I got this div via a inspect elment. Apparently this class 'ZINbbc'
        #has been around since 2018 so hopefully it doesn't deprecate soon...
        for link in googleSoup.find_all('div', attrs={'class': 'ZINbbc'}):
            try:
                url = link.find("a", href=True)
                urlResults.append(url['href'])
            except:
                pass
        return self._urlResultCleanup(urlResults)

    def _urlResultCleanup(self, urlResults):
        cleanedUrls = []
        for url in urlResults:
            #remove the random stuff google adds before https
            #Yeah it also removes https:// but that doesn't affect
            #my usecase so it doesn't matter

            cleaned = url.partition("://")[-1]
            # the & is the junk google adds at the end of urls
            cleaned = cleaned.partition("&")[0]

            #filter out some random empty urls i was getting
            if len(cleaned) > 10 and not (cleaned in cleanedUrls):
                cleanedUrls.append(cleaned)
        #use the following commented code to check cleaned urls
        # for i in cleanedUrls:
        #     print("URL: ", i)
        #     print('\n')

        return(cleanedUrls)

    def getText(self, soup):
        paragraphs = soup.find_all('p')
        # get text from each paragraph
        text = [para.getText() for para in paragraphs]
        text = [t for t in text if len(t) > 30]  # filter short unwanted text
        text = " ".join(text)  # join it

        # print(text)
        return text

    def getNewsProvider(self, url):
        first = "www."
        last = "."
        try:
            start = url.index(first) + len(first)
            end = url.index(last, (start+1))
            return (url[start:end]).upper()
        except ValueError:
            return ""

    def getImage(self, soup):
        images = soup.findAll('img')
        for uri in images:
            try:
                if "png" in uri['src'] or "jpg" in uri['src'] or "jpeg" in uri['src']:
                    # req = urllib2.Request(
                    #     uri['src'], headers={"Range": "5000"})
                    # r = urllib2.urlopen(req)
                    # info, h, w = self.getImageInfo(r.read())
                    # if h > 200 and w > 200:
                    #     print("SUCCESS")
                    #     return uri['src']


                    # file = urllib.request.urlopen(uri['src'])
                    # size = file.headers.get("content-length")
                    # if size:
                    #     size = int(size)
                    # p = ImageFile.Parser()
                    # while True:
                    #     data = file.read(1024)
                    #     if not data:
                    #         break
                    #     p.feed(data)
                    #     if p.image:
                    #         if p.image.size[0] > 200 and p.image.size[1] > 200:
                    #             print("SUCCESS 2")
                    #             return uri['src']
                    #         break
                    # file.close()

                    r = requests.get(uri['src'], stream = True)
                    if r.status_code == 200:
                        r.raw.decode_content = True
                        toRet = False
                        with Image.open(r.raw) as img:
                            # print(np.shape(img))
                            if np.shape(img)[0] > 200 and np.shape(img)[1] > 200:
                                toRet = True
                        if toRet == True: 
                            print("returning")
                            return uri['src']
            except:
                pass
                    # print("no img")
        return "https://us.123rf.com/450wm/pavelstasevich/pavelstasevich1811/pavelstasevich181101027/112815900-stock-vector-no-image-available-icon-flat-vector.jpg?ver=6"

    def authenticate_client(self):
        # on a seperate git-ignored file
        ta_credential = AzureKeyCredential(azureKey.key)
        text_analytics_client = TextAnalyticsClient(
            endpoint=azureKey.endpoint, credential=ta_credential)
        return text_analytics_client

    def trimAzure(self, text):
        trimmed = text[0:5000]
        return trimmed

    def _getSentiment(self, client, text):

        return 0.5  # TEMP

        documents = [text]
        response = client.analyze_sentiment(documents=documents)[0]
        print("Document Sentiment: {}".format(response.sentiment))
        print("Overall scores: positive={0:.2f}; neutral={1:.2f}; negative={2:.2f} \n".format(
            response.confidence_scores.positive,
            response.confidence_scores.neutral,
            response.confidence_scores.negative,
        ))

        return response.confidence_scores.positive + (response.confidence_scores.negative * -1)

    def _getRating(self, relatedNews, mainReadability, mainReadingTime, mainSentiment):

        counter = 0
        avgReadability = 0
        avgReadingTime = 0
        avgSentiment = 0
        for elem in relatedNews:
            avgReadability += elem.get("readability")
            avgReadingTime += elem.get("readingTime")
            avgSentiment += elem.get("sentiment")
            counter += 1
        avgReadability = avgReadability/counter
        avgReadingTime = avgReadingTime/counter
        avgSentiment = avgSentiment/counter

        # the 0.000001 is to avoid div by 0
        finalRating = self._computeRating(
            mainSentiment, mainReadability, mainReadingTime, avgSentiment, avgReadability, avgReadingTime)

        otherNewsRating = []
        for news in relatedNews:
            rating = self._computeRating(
                news.get("sentiment"), news.get("readability"), news.get("readingTime"), avgSentiment, avgReadability, avgReadingTime)
            otherNewsRating.append(rating)
            news['rating'] = rating

        orderedNews = []
        for _ in range(len(relatedNews)):
            idx = np.argmax(otherNewsRating)
            orderedNews.append(relatedNews[idx])
            otherNewsRating[idx] = -100

        return finalRating, orderedNews

    def _computeRating(self, sentimentIn, readabilityIn, timeIn, sentiment, readability, time):
        sentimentRating = (
            (((sentimentIn + 1)/2) / (((sentiment + 1)/2)+0.000001)) - 1) * 1.5  # sensitive to 66%
        sentimentRating = np.clip([sentimentRating], -1, 1)[0]

        readabilityRating = (
            (readabilityIn / readability + 0.0000001) - 1) * 2.5  # sensitive up to 40%
        readabilityRating = np.clip([readabilityRating], -1, 1)[0]

        readingTimeRating = (
            (time/(timeIn + 0.00001)) - 1) * 2  # sensitive up to 50%
        readingTimeRating = np.clip([readingTimeRating], -1, 1)[0]

        finalRating = ((sentimentRating + readabilityRating +
                        readingTimeRating + 3) / 6)

        return finalRating

    # def getImageInfo(self, data):
    #     data = data
    #     size = len(data)
    #     #print(size)
    #     height = -1
    #     width = -1
    #     content_type = ''

    #     # handle GIFs
    #     if (size >= 10) and data[:6] in (b'GIF87a', b'GIF89a'):
    #         # Check to see if content_type is correct
    #         content_type = 'image/gif'
    #         w, h = struct.unpack(b"<HH", data[6:10])
    #         width = int(w)
    #         height = int(h)

    #     # See PNG 2. Edition spec (http://www.w3.org/TR/PNG/)
    #     # Bytes 0-7 are below, 4-byte chunk length, then 'IHDR'
    #     # and finally the 4-byte width, height
    #     elif ((size >= 24) and data.startswith(b'\211PNG\r\n\032\n')
    #         and (data[12:16] == b'IHDR')):
    #         content_type = 'image/png'
    #         w, h = struct.unpack(b">LL", data[16:24])
    #         width = int(w)
    #         height = int(h)

    #     # Maybe this is for an older PNG version.
    #     elif (size >= 16) and data.startswith(b'\211PNG\r\n\032\n'):
    #         # Check to see if we have the right content type
    #         content_type = 'image/png'
    #         w, h = struct.unpack(b">LL", data[8:16])
    #         width = int(w)
    #         height = int(h)

    #     # handle JPEGs
    #     elif (size >= 2) and data.startswith(b'\377\330'):
    #         content_type = 'image/jpeg'
    #         jpeg = io.BytesIO(data)
    #         jpeg.read(2)
    #         b = jpeg.read(1)
    #         try:
    #             while (b and ord(b) != 0xDA):
    #                 while (ord(b) != 0xFF):
    #                     b = jpeg.read(1)
    #                 while (ord(b) == 0xFF):
    #                     b = jpeg.read(1)
    #                 if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
    #                     jpeg.read(3)
    #                     h, w = struct.unpack(b">HH", jpeg.read(4))
    #                     break
    #                 else:
    #                     jpeg.read(int(struct.unpack(b">H", jpeg.read(2))[0])-2)
    #                 b = jpeg.read(1)
    #             width = int(w)
    #             height = int(h)
    #         except struct.error:
    #             pass
    #         except ValueError:
    #             pass

    #     return content_type, width, height

#This main funciton is just for debugging


if __name__ == "__main__":
    a = WebProcessor()
    print(a.getUrlData("https://www.bbc.com/news/world-us-canada-53129524"))
