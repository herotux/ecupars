import requests

class LimoSMSClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.limosms.com/api"

    def send_sms(self, sender_number, message, mobile_numbers, send_to_blocks_number=False, send_time_span=None):
        url = f"{self.base_url}/sendsms"
        payload = {
            "SenderNumber": sender_number,
            "Message": message,
            "MobileNumber": mobile_numbers,
            "SendToBlocksNumber": send_to_blocks_number,
            "SendTimeSpan": send_time_span
        }
        headers = {"ApiKey": self.api_key}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def send_peer_to_peer_sms(self, sender_number, messages, mobile_numbers, send_to_blocks_number=False, send_time_span=None):
        url = f"{self.base_url}/sendpeertopeersms"
        payload = {
            "SenderNumber": sender_number,
            "Message": messages,
            "MobileNumber": mobile_numbers,
            "SendToBlocksNumber": send_to_blocks_number,
            "SendTimeSpan": send_time_span
        }
        headers = {"ApiKey": self.api_key}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def send_pattern_message(self, otp_id, replace_tokens, mobile_number):
        url = f"{self.base_url}/sendpatternmessage"
        payload = {
            "OtpId": otp_id,
            "ReplaceToken": replace_tokens,
            "MobileNumber": mobile_number
        }
        headers = {"ApiKey": self.api_key}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def send_verification_code(self, mobile, footer=None):
        url = f"{self.base_url}/sendcode"
        payload = {
            "Mobile": mobile,
            "Footer": footer
        }
        headers = {"ApiKey": self.api_key}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def check_verification_code(self, mobile, code):
        url = f"{self.base_url}/checkcode"
        payload = {
            "Mobile": mobile,
            "Code": code
        }
        headers = {"ApiKey": self.api_key}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def get_received_messages(self, number, page=1, size=100):
        url = f"{self.base_url}/getreceivedmessage"
        payload = {
            "Number": number,
            "Page": page,
            "Size": size
        }
        headers = {"ApiKey": self.api_key}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def get_message_status(self, message_ids):
        url = f"{self.base_url}/getstatus"
        payload = {
            "MessageId": message_ids
        }
        headers = {"ApiKey": self.api_key}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def get_profile_info(self):
        url = f"{self.base_url}/getcurrentcredit"
        headers = {"ApiKey": self.api_key}
        response = requests.post(url, json={}, headers=headers)
        return response.json()