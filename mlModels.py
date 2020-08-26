from tensorflow import keras
from tensorflow.keras.models import load_model
import numpy as np
import codecs
import re
#INCOMPLETE: THIS FILE WILL LOAD MY TF TRAINED MODELS FOR PREDICITON

contraction_mapping = {"ain't": "is not", "aren't": "are not", "can't": "cannot", "'cause": "because", "could've": "could have", "couldn't": "could not",

                       "didn't": "did not", "doesn't": "does not", "don't": "do not", "hadn't": "had not", "hasn't": "has not", "haven't": "have not",

                       "he'd": "he would", "he'll": "he will", "he's": "he is", "how'd": "how did", "how'd'y": "how do you", "how'll": "how will", "how's": "how is",

                       "I'd": "I would", "I'd've": "I would have", "I'll": "I will", "I'll've": "I will have", "I'm": "I am", "I've": "I have", "i'd": "i would",

                       "i'd've": "i would have", "i'll": "i will",  "i'll've": "i will have", "i'm": "i am", "i've": "i have", "isn't": "is not", "it'd": "it would",

                       "it'd've": "it would have", "it'll": "it will", "it'll've": "it will have", "it's": "it is", "let's": "let us", "ma'am": "madam",

                       "mayn't": "may not", "might've": "might have", "mightn't": "might not", "mightn't've": "might not have", "must've": "must have",

                       "mustn't": "must not", "mustn't've": "must not have", "needn't": "need not", "needn't've": "need not have", "o'clock": "of the clock",

                       "oughtn't": "ought not", "oughtn't've": "ought not have", "shan't": "shall not", "sha'n't": "shall not", "shan't've": "shall not have",

                       "she'd": "she would", "she'd've": "she would have", "she'll": "she will", "she'll've": "she will have", "she's": "she is",

                       "should've": "should have", "shouldn't": "should not", "shouldn't've": "should not have", "so've": "so have", "so's": "so as",

                       "this's": "this is", "that'd": "that would", "that'd've": "that would have", "that's": "that is", "there'd": "there would",

                       "there'd've": "there would have", "there's": "there is", "here's": "here is", "they'd": "they would", "they'd've": "they would have",

                       "they'll": "they will", "they'll've": "they will have", "they're": "they are", "they've": "they have", "to've": "to have",

                       "wasn't": "was not", "we'd": "we would", "we'd've": "we would have", "we'll": "we will", "we'll've": "we will have", "we're": "we are",

                       "we've": "we have", "weren't": "were not", "what'll": "what will", "what'll've": "what will have", "what're": "what are",

                       "what's": "what is", "what've": "what have", "when's": "when is", "when've": "when have", "where'd": "where did", "where's": "where is",

                       "where've": "where have", "who'll": "who will", "who'll've": "who will have", "who's": "who is", "who've": "who have",

                       "why's": "why is", "why've": "why have", "will've": "will have", "won't": "will not", "won't've": "will not have",

                       "would've": "would have", "wouldn't": "would not", "wouldn't've": "would not have", "y'all": "you all",

                       "y'all'd": "you all would", "y'all'd've": "you all would have", "y'all're": "you all are", "y'all've": "you all have",

                       "you'd": "you would", "you'd've": "you would have", "you'll": "you will", "you'll've": "you will have",

                       "you're": "you are", "you've": "you have"}


class Predictor:
    def __init__(self):
        self.sarcasmModel = load_model("./sarcasmModel.h5")
        glove = './glove.6B.50d'
        f = codecs.open(glove + ".txt", 'r', encoding='utf-8')
        model = {}
        for line in f:
            split_line = line.split()
            word = split_line[0]
            embedding = np.array([float(val) for val in split_line[1:]])
            model[word] = embedding
        self.glove = model


    def predict(self, input):
        processed = self.process(input)
        if processed == "error":
            return {"sarcasm": "error", "category": "error"}
        sarcasm = self.sarcasmModel.predict(processed)
        return {"sarcasm":sarcasm, "category": "category"}


    def process(self, text):
        processedText = self.preprocess(text)
        vectors = self.get_w2v(processedText, self.glove)
        padded = self.padZeros(vectors)
        if padded == "skip":
            return "error"
        padded = np.array(padded)
        padded = np.reshape(padded, (1,25,50))
        return padded

    def get_w2v(self, sentence, model):
        return np.array([model.get(val, np.zeros(50)) for val in sentence.split()], dtype=np.float64)


    def preprocess(self, input):
        if type(input) != type("string"):
            return "skip"
        input = input.lower()
        if input in contraction_mapping.keys():
            input = contraction_mapping.get(input)
        input = re.sub(r"[^A-Za-z0-9^,!.\/'+-=]", " ", input)
        input = re.sub(r"what's", "what is ", input)
        input = re.sub(r"\'s", " ", input)
        input = re.sub(r"\'ve", " have ", input)
        input = re.sub(r"can't", "cannot ", input)
        input = re.sub(r"n't", " not ", input)
        input = re.sub(r"i'm", "i am ", input)
        input = re.sub(r"\'re", " are ", input)
        input = re.sub(r"\'d", " would ", input)
        input = re.sub(r"\'ll", " will ", input)
        input = re.sub(r",", " ", input)
        input = re.sub(r"\.", " ", input)
        input = re.sub(r"!", " ! ", input)
        input = re.sub(r"\/", " ", input)
        input = re.sub(r"\^", " ^ ", input)
        input = re.sub(r"\+", " + ", input)
        input = re.sub(r"\-", " - ", input)
        input = re.sub(r"\=", " = ", input)
        input = re.sub(r"'", " ", input)
        input = re.sub(r"(\d+)(k)", r"\g<1>000", input)
        input = re.sub(r":", " : ", input)
        input = re.sub(r" e g ", " eg ", input)
        input = re.sub(r" b g ", " bg ", input)
        input = re.sub(r" u s ", " american ", input)
        input = re.sub(r"\0s", "0", input)
        input = re.sub(r" 9 11 ", "911", input)
        input = re.sub(r"e - mail", "email", input)
        input = re.sub(r"j k", "jk", input)
        input = re.sub(r"\s{2,}", " ", input)
        return input


    def padZeros(self, input):
        maxLen = 25
        if len(input) >= maxLen or len(input) < 4:
            return "skip"
        if np.shape(input)[0] == maxLen:
            return input
        lenToPad = maxLen - np.shape(input)[0]
        output = np.concatenate((input, np.zeros((lenToPad, 50))))
        return output
        return np.transpose(output)

if __name__ == "__main__":
    predictor = Predictor()
    print(predictor.predict(
        "New Environmentally Friendly Burial Involves Having Your Dead Body Eaten By Wealthy German Man With Taste For The Exotic"))
