# import nltk as nltk
# nltk.download('punkt')
from textstat import textstat


class TextPredicor:
    def __init__(self):
        ########Constants########
        self.wpm = 250
        ########Constants########

    def getTextResults(self, text):
        #Text needs to be a string
        # splitText = nltk.tokenize.sent_tokenize(text) #split it
        readTime = self._getReadTime(text)
        readability = self._getReadability(text)
        return {
            "readTime": readTime,
            "readability": readability
        }
    def _getReadTime(self, text):
        counter = len(text.split())
        return counter/self.wpm
    def _getReadability(self, text):
        # print("Reading scores: ", textstat.flesch_reading_ease(text))
        return textstat.flesch_reading_ease(text)
