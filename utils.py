import requests
import base64
import pandas
from config import CLIENT_ID, CLIENT_SECRET, BASE_URL


class ImportUtils:

    @staticmethod
    def authorize():
        client_id = CLIENT_ID
        client_secret = CLIENT_SECRET
        if client_id is None or client_secret is None:
            raise Exception('Authorization Failed: Please verify you have CLIENT_ID and CLIENT_SECRET set in the config module')

        encoded_credentials = ImportUtils.encode_credentials(client_id, client_secret)
        response = requests.post(
            BASE_URL + '/auth/client/token',
            headers={'Authorization': encoded_credentials},
        )

        if response.status_code == 200:
            response_json = response.json()
            return response_json['access_token']
        else:
            raise Exception('Authorization Failed: Please verify your CLIENT_ID and CLIENT_SECRET are valid in the config module')

    @staticmethod
    def encode_credentials(client_id, client_secret):
        client_credential_string = client_id + ':' + client_secret
        encoded_credentials = base64.b64encode(client_credential_string.encode("utf-8"))
        encoded_credentials_string = str(encoded_credentials, "utf-8")
        return 'Basic ' + encoded_credentials_string

    @staticmethod
    def get_csv_users(locked_users):
        users = pandas.read_csv('newark-users.csv')
        if not users.empty:
            users = users.to_dict('records')
            non_locked_users = ImportUtils.filter_locked_users_from_import(users, locked_users)
            return non_locked_users
        else:
            raise Exception('Failed to parse CSV file containing users')

    @staticmethod
    def get_email_message(body):
        return f"""
        <html>
          <table width='auto' cellpadding='10'>
            <thead style='text-align: left;'>
              <tr>
                <th>Newark User Import Summary</th>
              </tr>
            </thead>
            <tbody style='text-align: left;'>
              <tr>
                  <td>{body}</td>
              </tr>
            </tbody>
          </table>
        </html>
        """

    @staticmethod
    def get_whetstone_roles(role_to_convert, user_type, roles):
        whetstone_roles = []
        role_map = {
            "0": ["Teacher"],
            "#N/A": ["Teacher"],
            "Adult Support Framework": ["Teacher", "Coach"],
            "CST Framework": ["Teacher"],
            "Director / Supervisor": ["Teacher"],
            "Framework for Effective Teaching": ["Teacher"],
            "Non-instructional": ["Teacher"],
            "NPS non-Principal Leadership Framework": ["School Assistant Admin"],
            "NPS Principal Framework": ["School Assistant Admin"],
            "Nurse Framework": ["Teacher"],
            "Paraprofessional": ["Teacher"],
            "School-Wide Services Framework": ["Teacher"],
            "Student Support Framework": ["Teacher"],
            "Unaffiliated": ["Teacher"]
        }

        # if the role to convert isn't a string we default them to teacher
        if not isinstance(role_to_convert, str):
            role_to_convert = "#N/A"
        whetstone_role_names = role_map[role_to_convert]

        for whetstone_role_name in whetstone_role_names:
            whetstone_roles.append(ImportUtils.find_object(whetstone_role_name, 'name', roles))

        # Check User Type for one of the Department Chair job titles, if it exists the user get department chair role
        department_chair_job_titles = ["D/C English", "D/C Math", "D/C Science", "D/C Social Studies", "D/C Health/Physical Education", "D/C Visual and Performing Arts", "D/C Bilingual", "D/C Special Education"]
        if user_type in department_chair_job_titles:
            whetstone_roles.append(ImportUtils.find_object("Department Chair", 'name', roles))

        if len(whetstone_roles):
            whetstone_roles = list(map(lambda role: role['_id'], whetstone_roles))
        return whetstone_roles

    @staticmethod
    def filter_locked_users_from_import(users_to_import, locked_users):
        if len(locked_users):
            def get_id(user):
                # Make sure the user has an internal ID and its not blank
                if 'internalId' in user and user['internalId']:
                    # Return the ID as a number
                    return int(user['internalId'])
                else:
                    return 0
            locked_obj = map(lambda user: get_id(user), locked_users)
            locked_user_ids = list(locked_obj)
            filter_obj = filter(lambda user: 'Emplid' in user and user['Emplid'] not in locked_user_ids, users_to_import)
            filtered_list = list(filter_obj)
            return filtered_list
        else:
            return users_to_import

    @staticmethod
    def get_locked_group_members(group, role, locked_user_ids):
        group_members = group[role]
        if group_members:
            return list(filter(lambda user: user in locked_user_ids, group_members))
        else:
            return []

    @staticmethod
    def get_users_to_archive(users_to_import, existing_users):
        user_id_obj = map(lambda user: user["Emplid"], users_to_import)
        user_ids = list(user_id_obj)

        def user_missing(user):
            not_multi_district = len(user['districts']) < 2
            not_archived = 'archivedAt' in user and user['archivedAt'] is None
            not_in_import = 'internalId' in user and user['internalId'] is not None and user['internalId'] not in user_ids
            not_locked = 'locked' in user and user['locked'] is not True or 'locked' not in user
            return not_multi_district and not_archived and not_in_import and not_locked
        missing_users = list(filter(lambda user: user_missing(user), existing_users))
        for missing_user in missing_users:
            print(f'Archiving User {missing_user["name"]}')
        missing_user_ids = list(map(lambda user: user["_id"], missing_users))
        return missing_user_ids

    @staticmethod
    def create_default_groups(school):
        if 'observationGroups' not in school:
            school['observationGroups'] = []
        group_names = list(map(lambda group: group['name'], school['observationGroups']))
        if 'Non-Instructional Staff' not in group_names:
            school['observationGroups'].append({
                'name': 'Non-Instructional Staff',
                'observers': [],
                'observees': []
            })
        if 'Instructional Staff' not in group_names:
            school['observationGroups'].append({
                'name': 'Instructional Staff',
                'observers': [],
                'observees': []
            })

    @staticmethod
    def add_user_to_school_position(user, user_id, school):
        non_instructional_group = ImportUtils.find_object('Non-Instructional Staff', 'name', school['observationGroups'])
        instructional_group = ImportUtils.find_object('Instructional Staff', 'name', school['observationGroups'])
        user_role = user['Framework']
        # TODO: Figure out where Director/Supervisor goes
        if user_role in {'0', '#N/A', 'CST Framework', 'Non-instructional', 'Nurse Framework', 'School-Wide Services', 'Student Support Framework', 'Unaffiliated'}:
            non_instructional_group['observees'].append(user_id)
        if user_role == 'Adult Support Framework':
            instructional_group['observees'].append(user_id)
            instructional_group['observers'].append(user_id)
        if user_role in {'Framework for Effective Teaching', 'Paraprofessional'}:
            instructional_group['observees'].append(user_id)
        if user_role == 'NPS non-Principal Leadership Framework':
            school['assistantAdmins'].append(user_id)
        if user_role == 'NPS Principal Framework':
            school['admins'].append(user_id)

    @staticmethod
    def add_practice_user_to_school(practice_user, school):
        practice_user_id = practice_user['_id']
        non_instructional_group = ImportUtils.find_object('Non-Instructional Staff', 'name', school['observationGroups'])
        instructional_group = ImportUtils.find_object('Instructional Staff', 'name', school['observationGroups'])
        if ImportUtils.find_object(practice_user_id, 'observees', non_instructional_group) is None:
            non_instructional_group.observees.append(practice_user_id)
        if ImportUtils.find_object(practice_user_id, 'observees', instructional_group) is None:
            instructional_group.observees.append(practice_user_id)

    @staticmethod
    def find_string(element_to_find, list_to_search):
        try:
            element_index = list_to_search.index(element_to_find)
            return list_to_search[element_index]
        except ValueError:
            return None

    @staticmethod
    def find_object(value_to_find, property_name, list_to_search):
        found_object = None
        for x in list_to_search:
            if property_name in x and x[property_name] == value_to_find:
                found_object = x
        return found_object
