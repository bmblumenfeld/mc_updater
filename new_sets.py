import requests
from twilio.rest import Client
import config

MISSION_CLIFFS_ENDPONT = config.MISSION_CLIFFS_ENDPONT
IG_POST_ENDPOINT = config.IG_POST_ENDPOINT
TWILIO_SID = config.TWILIO_SID
TWILIO_AUTH_TOKEN = config.TWILIO_AUTH_TOKEN
TWILIO_TRIAL_NUMBER = config.TWILIO_TRIAL_NUMBER
NUMBERS = config.NUMBERS #list of numbers that will recieve text
MOST_RECENT_POST_PATH = './most_recent_post.txt'
NEW_ROUTE_KEYWORDS = [

    "new",
    "fresh",
    "set",
    "routes",
    "attention",
    "reminder",
    "closed",

]


def is_new_route_match(caption):
    caption  = caption.lower()
    is_possible_new_route = False
    for keyword in NEW_ROUTE_KEYWORDS:
        if caption.find(keyword) > 0:
            is_possible_new_route = True
    return is_possible_new_route
    

def get_mc_most_recent_post_caption_text(mc_profile_html_text):
    post_short_code = get_mc_most_recent_post_uuid(mc_profile_html_text)
    caption_keyword = "\"edge_media_to_caption\":{\"edges\":[{\"node\":{\"text\":\""
    pic_keyword = "\\"
    post_text_start_index = mc_profile_html_text.find(caption_keyword) + len(caption_keyword)
    post_text_end_index = post_text_start_index + mc_profile_html_text.find(post_short_code)
    post_text = mc_profile_html_text[post_text_start_index:post_text_end_index]
    caption_end_index = post_text.find(pic_keyword)
    caption = post_text[0:caption_end_index]
    return caption


def get_mc_most_recent_post_uuid(mc_profile_html_text):
    short_code_len = 11
    short_code_keyword = "\"shortcode\":\""
    mc_profile_html_text = requests.get(MISSION_CLIFFS_ENDPONT).text
    short_code_start_index = mc_profile_html_text.find(short_code_keyword) + len(short_code_keyword)
    short_code_end_index = short_code_start_index + short_code_len
    return mc_profile_html_text[short_code_start_index:short_code_end_index]


def update_local_post_uuid(new_uuid):
    most_recent_post_file = open(MOST_RECENT_POST_PATH, "w")
    most_recent_post_file.write(new_uuid)
    most_recent_post_file.close()


def get_local_post_uuid():
    most_recent_post_file = open(MOST_RECENT_POST_PATH, "r")
    uuid = most_recent_post_file.read()
    most_recent_post_file.close()
    return uuid


def main():
    mc_profile_html_text = requests.get(MISSION_CLIFFS_ENDPONT).text
    most_recent_post_uuid = get_mc_most_recent_post_uuid(mc_profile_html_text)
    local_uuid = get_local_post_uuid()
    if most_recent_post_uuid == local_uuid:
        return
    update_local_post_uuid(most_recent_post_uuid)
    most_recent_caption = get_mc_most_recent_post_caption_text(mc_profile_html_text)
    if is_new_route_match(most_recent_caption):
        for number in NUMBERS:
            print(f'ATTEMPTING TO SEND MESSAGE TO: {number}')
            client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
            try:
                message = client.messages.create(
                to=number,
                from_=TWILIO_TRIAL_NUMBER,
                body=f"SHIT IS GOING ON AT MC~~ \n {most_recent_caption}")
            except:
                print("ROBOT IT HAVING ISSUES")
                raise


if __name__ == "__main__":
	main()