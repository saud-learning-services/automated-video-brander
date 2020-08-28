import requests
import json
import os
import youtube_dl

PANOPTO_BASE = "https://ubc.ca.panopto.com"

"""
Place the value of your .ASPXAUTH token in the following variable
"""
TOKEN = '795D9A4FC5ACEC5412CB054597EC3BE95E0DB17842E32FA82990B3671956963D7741004EE2BF5CB48757C510C5BF18284F836A17D61DDE31EFB586067FF5F0E19606FD73463D87C0CF7F7C57CF2F3902CC90D9D332BEAEE78650FA1737D6392CA185B9D9807977EBA3A549BE435175CDC2E74BEF207CE0477E5DAA4F178A54223D6A11121CECF76E9D0A97DC3424AD9812F91C53D435FDED5BF47D95226CF36B138E6BE4412A8B94DA451672C7E036CB1F88D1A36739B9A75E0AF755582A525A5C79D4FFC56DE1A6AAC3A0F70B76CB4545183B681B870C51963CE0BE79AE7115671EDD0E40427B38D1E5E34EC108E9D8'

s = requests.session()  # cheeky global variable
s.cookies = requests.utils.cookiejar_from_dict({".ASPXAUTH": TOKEN})

# WHYYYY does panopto use at least 3 different types of API!?!?!?


def json_api(endpoint, params=dict(), post=False, paramtype="params"):
    if post:
        r = s.post(PANOPTO_BASE + endpoint, **{paramtype: params})
    else:
        r = s.get(PANOPTO_BASE + endpoint, **{paramtype: params})
    if not r.ok:
        print(r.text)
    return json.loads(r.text)


def name_normalize(name):
    return name.replace("/", "-")


def dl_session(delivery_id):
    dest_dir = "downloads"
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    print('checkpoint 1')
    delivery_info = json_api("/Panopto/Pages/Viewer/DeliveryInfo.aspx", {
        "deliveryId": delivery_id,
        "responseType": "json"
    }, True, "data")
    print(delivery_info)
    streams = delivery_info["Delivery"]["Streams"]
    for i in range(len(streams)):
        filename = "{:02d}_{}.mp4".format(i, streams[i]["Tag"])
        dest_filename = os.path.join(dest_dir, filename)
        print("Downloading:", dest_filename)
        ydl_opts = {
            "outtmpl": dest_filename,
            "quiet": True
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([streams[i]["StreamUrl"]])


DELIVERY_ID = '96b10708-13a3-4254-8bdc-ac240138eee8'
dl_session(DELIVERY_ID)

# def dl_folder(folder):
#     sessions = json_api("/Panopto/Services/Data.svc/GetSessions", {
#         "queryParameters": {
#             "folderID": folder["Id"],
#         }
#     }, True, "json")["d"]["Results"]

#     for session in sessions:
#         dl_session(session)


# folders = json_api("/Panopto/Api/v1.0-beta/Folders", {
#     "parentId": "null",
#     "folderSet": 1
# })

# for folder in folders:
#     """
#             Put an if statement here based on folder["Name"] if you just want a certain
#             module or year etc.
#             e.g.:
#     """
#     if folder["Name"].startswith("1819"):
#         dl_folder(folder)
