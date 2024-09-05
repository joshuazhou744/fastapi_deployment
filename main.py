from fastapi import FastAPI
import motor.motor_asyncio
import pprint
from fastapi.middleware.cors import CORSMiddleware

from model import Climb
from dotenv import load_dotenv
import os

if os.environ.get("VERCEL_ENV") is None:
    load_dotenv(dotenv_path='.env.local')
    DATABASE_URI = os.getenv("DATABASE_URI")
else:
    DATABASE_URI = os.environ.get("DATABASE_URI")

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


client = None
def get_db():
    global client
    if not client:
        client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URI, maxPoolSize=10, serverSelectionTimeoutMS=5000)
    return client["test_db"]

def get_climb_collection():
    client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URI)
    db = client["test_db"]
    return db["climbs"]

@app.get("/climbs/")
async def get_all_climbs():
    collection = get_climb_collection()
    cursor = collection.find({})  
    climbs = []
    async for document in cursor:
        document["_id"] = str(document["_id"])
        climbs.append(document)
    return climbs

@app.post("/climbs/")
async def post_climb(climb: Climb):
    document = climb.dict()
    collection = get_climb_collection()
    result = await collection.insert_one(document)
    return str(result.inserted_id)

@app.put("/climbs/{title}/{climb_id}/")
async def add_id(title: str, climb_id: int):
    collection = get_climb_collection()
    old_document = await collection.find_one({"title": title})
    print("found document: %s" % pprint.pformat(old_document))
    _id = old_document["_id"]
    result = await collection.replace_one({"_id": _id}, {"climb_id": climb_id, **old_document})
    print("replaced %s document" % result.modified_count)
    new_document = await collection.find_one({"_id": _id})
    print("document is now %s" % pprint.pformat(new_document))
    return str(new_document)

@app.get("/climbs/{title}/")
async def test_get(title: str):
    collection = get_climb_collection()
    result = await collection.find_one({"title": title})
    if result is None:
        result = ("404 not found")
    pprint.pprint(result)
    return str(result)


@app.put("/climbs/{climb_id}/{new_title}")
async def change_title(climb_id: int, new_title: str):
    collection = get_climb_collection()
    result = await collection.update_one({"climb_id": climb_id}, {"$set": {"title": new_title}})
    print("updated %s document" % result.modified_count)
    new_document = await collection.find_one({"title": new_title})
    print("document is now %s" % pprint.pformat(new_document))
    return str(new_document)

@app.delete("/climbs/{title}}")
async def del_climb(title: str):
    collection = get_climb_collection() 
    n = await collection.count_documents({})
    print("%s documents before calling delete_one()" % n)
    result = await collection.delete_one({"title": title})
    print("%s documents after" % (n))
    return str(result)