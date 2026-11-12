import uuid
from django.conf import settings
import onesignal
from onesignal.api import default_api

def send_notification(message):
    configuration = onesignal.Configuration(
        rest_api_key=settings.ONESIGNAL_REST_API_KEY,
    )

    notification = onesignal.Notification(
        app_id=settings.ONESIGNAL_APP_ID,
        external_id=str(uuid.uuid4()),
        contents=onesignal.StringMap(en=message),
        is_any_web=True,
        included_segments=['Subscribed Users'],
    )

    with onesignal.ApiClient(configuration) as api_client:
        api_instance = default_api.DefaultApi(api_client)
        response = api_instance.create_notification(notification)

    return response

# import uuid
# from django.conf import settings
# from onesignal import Configuration, ApiClient
# from onesignal.api import default_api
# from onesignal.model.notification import Notification
# from onesignal.model.string_map import StringMap

# def send_notification(message):
#     # Configure OneSignal API client
#     configuration = Configuration(
#         app_key=settings.ONESIGNAL_APP_KEY,
#         user_key=settings.ONESIGNAL_USER_KEY
#     )

#     # Create a notification object
#     notification = Notification()
#     notification.set_attribute('app_id', settings.ONESIGNAL_APP_ID)
#     notification.set_attribute('external_id', str(uuid.uuid4()))

#     # Add content
#     contents = StringMap()
#     contents.set_attribute('en', message)
#     notification.set_attribute('contents', contents)

#     # Target audience (update as per your needs)
#     notification.set_attribute('is_any_web', True)
#     notification.set_attribute('included_segments', ['Subscribed Users'])

#     # Send the notification
#     with ApiClient(configuration) as api_client:
#         api_instance = default_api.DefaultApi(api_client)
#         response = api_instance.create_notification(notification)

#     return response
