from pymongo import MongoClient
from datetime import datetime, timedelta
from config import MONGO_URI, DB_NAME, FREE_CREDITS

# ============ MONGODB CONNECTION ============
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users_col = db["users"]
premium_col = db["premium_requests"]

users_col.create_index("user_id", unique=True)
premium_col.create_index("user_id", unique=True)


# ============ USER FUNCTIONS ============
def get_user(user_id):
    user = users_col.find_one({"user_id": user_id})
    if not user:
        new_user = {
            "user_id": user_id,
            "name": "",
            "username": "",
            "downloads": 0,
            "total_downloads": 0,
            "credits": FREE_CREDITS,
            "premium": False,
            "premium_expiry": None,
            "joined": datetime.now(),
            "last_active": datetime.now()
        }
        users_col.insert_one(new_user)
        return new_user
    return user


def update_user(user_id, **kwargs):
    kwargs["last_active"] = datetime.now()
    users_col.update_one({"user_id": user_id}, {"$set": kwargs}, upsert=True)
    return get_user(user_id)


def increment_download(user_id):
    users_col.update_one(
        {"user_id": user_id},
        {"$inc": {"downloads": 1, "total_downloads": 1},
         "$set": {"last_active": datetime.now()}},
        upsert=True
    )
    return get_user(user_id)


def decrement_credit(user_id):
    user = get_user(user_id)
    if user.get("credits", 0) > 0:
        users_col.update_one(
            {"user_id": user_id},
            {"$inc": {"credits": -1}, "$set": {"last_active": datetime.now()}}
        )
    return get_user(user_id)


def add_credits(user_id, amount):
    users_col.update_one(
        {"user_id": user_id},
        {"$inc": {"credits": amount}, "$set": {"last_active": datetime.now()}},
        upsert=True
    )
    return get_user(user_id)


def get_all_users():
    users = list(users_col.find({}))
    return {str(u["user_id"]): u for u in users}


def get_total_users_count():
    return users_col.count_documents({})


def get_premium_users_count():
    return users_col.count_documents({"premium": True})


# ============ PREMIUM FUNCTIONS ============
def set_premium(user_id, days):
    expiry = datetime.now() + timedelta(days=days)
    users_col.update_one(
        {"user_id": user_id},
        {"$set": {"premium": True, "premium_expiry": expiry,
                  "credits": 999999, "last_active": datetime.now()}},
        upsert=True
    )
    return get_user(user_id)


def check_premium(user_id):
    user = get_user(user_id)
    if not user.get("premium"):
        return False
    expiry = user.get("premium_expiry")
    if expiry and datetime.now() > expiry:
        users_col.update_one(
            {"user_id": user_id},
            {"$set": {"premium": False, "premium_expiry": None, "credits": 0}}
        )
        return False
    return True


def get_premium_expiry(user_id):
    user = get_user(user_id)
    expiry = user.get("premium_expiry")
    if expiry:
        return expiry.strftime("%d-%m-%Y")
    return "N/A"


# ============ PREMIUM REQUESTS ============
def save_premium_request(user_id, data):
    data["user_id"] = user_id
    data["time"] = datetime.now()
    premium_col.update_one({"user_id": user_id}, {"$set": data}, upsert=True)


def get_premium_request(user_id):
    return premium_col.find_one({"user_id": user_id})


def get_all_premium_requests():
    return list(premium_col.find({}))


def delete_premium_request(user_id):
    premium_col.delete_one({"user_id": user_id})


def get_pending_count():
    return premium_col.count_documents({})