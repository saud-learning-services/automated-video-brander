import os
from dotenv import load_dotenv
from panopto.panopto_oauth2 import PanoptoOAuth2
from panopto.panopto_interface import Panopto

load_dotenv()

server = os.getenv('SERVER')
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

oauth2 = PanoptoOAuth2(server, client_id, client_secret, True)
panopto = Panopto(server, True, oauth2)

DELIVERY_ID = 'abcaf398-2a04-4c81-95bd-ac230151ff55'

panopto.download_video(DELIVERY_ID)
