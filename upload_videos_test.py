import os
from termcolor import cprint
from dotenv import load_dotenv
from helpers import load_specifications, get_video_attributes
from panopto.panopto_oauth2 import PanoptoOAuth2
from panopto.panopto_interface import Panopto

load_dotenv()

root = os.path.dirname(os.path.abspath(__file__))

specs = load_specifications(root + '/input')

server = os.getenv('SERVER')
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

oauth2 = PanoptoOAuth2(server, client_id, client_secret, True)

panopto = Panopto(server, True, oauth2)

panopto.upload_folder('output/BAMA/Class 8 DD1_Cluny South',
                      '942d5aa6-ea6e-48f8-8dd6-ac230170e0c9')

# panopto.upload_video('output/COMM 101/COMM 101 Test_Marko Prodanovic/primary.mp4',
#                      'a6e1ea0f-4095-432e-bdd2-ac2301231c01')
