import requests
from config import BASE_URL
from utils import ImportUtils


class ImportAPI:

    def __init__(self):
        self.auth_token = ImportUtils.authorize()
        self.district = None

    def get_headers(self):
        return {
            'Authorization': 'Bearer ' + self.auth_token,
            'district': self.district
        }

    def get_district(self, district_name):
        response = requests.get(
            f'{BASE_URL}/import/districts/{district_name}',
            headers=self.get_headers()
        )
        if response.status_code == 200:
            response_json = response.json()
            return response_json
        else:
            raise Exception('Failed to get district')

    def get_user(self, user_id):
        response = requests.get(
            BASE_URL + '/import/users/' + user_id,
            headers=self.get_headers()
        )
        if response.status_code == 200:
            response_json = response.json()
            return response_json
        else:
            raise Exception('Failed to get user')

    def get_practice_user(self):
        response = requests.get(
            BASE_URL + '/import/users/practice',
            headers=self.get_headers()
        )
        if response.status_code == 200:
            response_json = response.json()
            return response_json
        else:
            raise Exception('Failed to get practice user')

    def get_all_users(self):
        response = requests.get(
            BASE_URL + '/import/users?locked=false',
            headers=self.get_headers()
        )
        if response.status_code == 200:
            response_json = response.json()
            return response_json
        else:
            raise Exception('Failed to get all users')

    def get_locked_users(self):
        url = BASE_URL + '/import/users?locked=true'
        response = requests.get(
            url,
            headers=self.get_headers()
        )
        if response.status_code == 200:
            response_json = response.json()
            return response_json
        else:
            raise Exception('Failed to get locked users')

    def get_user_types(self):
        response = requests.get(
            BASE_URL + '/import/users/types',
            headers=self.get_headers()
        )
        if response.status_code == 200:
            response_json = response.json()
            return response_json
        else:
            raise Exception('Failed to get user types')

    def get_user_tags(self):
        response = requests.get(
            BASE_URL + '/import/users/tags',
            headers=self.get_headers()
        )
        if response.status_code == 200:
            response_json = response.json()
            return response_json
        else:
            raise Exception('Failed to get user types')

    def create_user(self, user):
        response = requests.post(
            BASE_URL + '/import/users',
            headers=self.get_headers(),
            json=user
        )
        if response.status_code == 201:
            response_json = response.json()
            return response_json
        else:
            raise Exception('Failed to create user')

    def update_user(self, update_user_id, fields_to_update):
        response = requests.put(
            BASE_URL + '/import/users/' + update_user_id,
            headers=self.get_headers(),
            json=fields_to_update
        )
        if response.status_code == 200:
            response_json = response.json()
            return response_json
        else:
            raise Exception('Failed to update user')

    def send_email(self, payload):
        response = requests.post(
            BASE_URL + '/import/emails',
            headers=self.get_headers(),
            json=payload
        )
        if response.status_code == 200:
            response_json = response.json()
            return response_json
        else:
            raise Exception('Failed to send email')

    def archive_users(self, users):
        response = requests.put(
            BASE_URL + '/import/users/archive',
            headers=self.get_headers(),
            json=users
        )
        if response.status_code == 200:
            response_json = response.json()
            return response_json
        else:
            raise Exception('Failed to archive users')

    def update_school(self, update_school_id, fields_to_update):
        response = requests.put(
            BASE_URL + '/import/schools/' + update_school_id,
            headers=self.get_headers(),
            json=fields_to_update
        )
        if response.status_code == 200:
            response_json = response.json()
            return response_json
        else:
            raise Exception('Failed to update school')

    def get_schools(self):
        response = requests.get(
            BASE_URL + '/import/schools',
            headers=self.get_headers()
        )
        if response.status_code == 200:
            response_json = response.json()
            return response_json
        else:
            raise Exception('Failed to get schools')

    def create_school(self, school):
        response = requests.post(
            BASE_URL + '/import/schools',
            headers=self.get_headers(),
            json=school
        )
        if response.status_code == 200:
            response_json = response.json()
            return response_json
        else:
            raise Exception('Failed to create school')

    def get_district_roles(self):
        response = requests.get(
            BASE_URL + '/import/roles',
            headers=self.get_headers()
        )
        if response.status_code == 200:
            response_json = response.json()
            return response_json
        else:
            raise Exception('Failed to get roles')
