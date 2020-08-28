import os
from dotenv import load_dotenv
from panopto.panopto_oauth2 import PanoptoOAuth2
from panopto.panopto_interface import Panopto
from helpers import load_specifications, get_video_attributes

load_dotenv()

root = os.path.dirname(os.path.abspath(__file__))

specs = load_specifications(root + '/input')

server = os.getenv('SERVER')
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

oauth2 = PanoptoOAuth2(server, client_id, client_secret, True)
panopto = Panopto(server, True, oauth2)

for index, row in specs.iterrows():
    print(
        '\n========================================================================\n')

    row = get_video_attributes(row)
    course = row['course']
    title = row['title']
    instructor = row['instructor']
    src_url = row['src_url']
    print(f'🎥 {course} | {title} | Row {index + 1}')

    filename = f'{title}_{instructor}.mp4'

    output_folder = f'{root}/input/body/{title}_{instructor}'

    delivery_id = src_url[-36:]

    try:
        panopto.download_video(delivery_id, output_folder)
    except Exception as err:
        print(err)
        continue
