from fastapi import FastAPI
import webhandler

app = FastAPI()
webprocessing = webhandler.WebProcessor()
#domain where this api is hosted for example : localhost:5000/docs to see swagger documentation automagically generated.


@app.get("/")
def home():
    return {"message":"debug test"}



@app.get("/ping/{url}")
async def pong(url: str):
    data = webprocessing.getUrlData(url)
    if data.get("error") != "none":
        return {"Bad inputs" : data.get("error")}
    
    return data

    # return {
    #     "Headline": data.get("headline"), 
    #     "readingscore": mainHeadlineScore,
    #     "relativeScore": relativeScore,
    #     "relatedScores": relatedScores
    #     }
    # return {"Headline": data.get("headline"), "Headline2": data.get("relatedHeadlines")}



#uvicorn API:api --reload

