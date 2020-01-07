import boto3
import config
import os
import requests
from twilio.rest import Client


# set as env variables lambda console
MISSION_CLIFFS_ENDPONT = os.getenv('MISSION_CLIFFS_ENDPONT')
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_TRIAL_NUMBER = os.getenv('TWILIO_TRIAL_NUMBER')
# list of numbers that will recieve text
NUMBERS = config.NUMBERS
BUCKET = os.getenv('BUCKET')
UUID_OBJECT_KEY = os.getenv('UUID_OBJECT_KEY')
S3 = boto3.resource('s3')
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
    caption = caption.lower()
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


def update_last_uuid(new_uuid, s3_object):
    """
    Updates s3 last checked uuid object
    """
    encoded_uuid = new_uuid.encode()
    s3_object.put(Body=encoded_uuid)


def get_last_uuid(s3_object):
    """
    Reaches out to s3 to get last uuid checked by this function.
    """
    s3_object_body = s3_object.get()["Body"]
    uuid = s3_object_body.read().decode('utf-8')
    return uuid


def main():
    mc_profile_html_text = requests.get(MISSION_CLIFFS_ENDPONT).text
    most_recent_post_uuid = get_mc_most_recent_post_uuid(mc_profile_html_text)
    most_recent_s3_object = S3.Object(BUCKET, UUID_OBJECT_KEY)
    last_uuid = get_last_uuid(most_recent_s3_object)
    if most_recent_post_uuid == last_uuid:
        return
    update_last_uuid(most_recent_post_uuid, most_recent_s3_object)
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


def mc_update_handler(event, context):
    try:
        main()
        return { 
            "status": "200"
        }
    except:
        raise