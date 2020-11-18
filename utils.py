import requests
import base64
import pandas
from config import CLIENT_ID, CLIENT_SECRET, BASE_URL


class ImportUtils:

    department_chair_job_titles = ["D/C English", "D/C Math", "D/C Science", "D/C Social Studies", "D/C Health/Physical Education", "D/C Visual and Performing Arts", "D/C Bilingual", "D/C Special Education"]
    nps_director_job_titles = ["Director", "Director Bilingual", "Director Early Childhood", "Director Health and Phys Ed", "Director Mathematics", "Director of Attendance", "Director of Students 2 Science", "Director Social Studies", "Director Special Education", "Director Staff Development", "Director Student Support Serv", "Director Support Services", "Director Visual/Performing Art", "Exec Dir Fed Programs & Grants", "Exec Dir Off Erly Chdhood", "Executive Director", "Executive Director of IT", "Director of Enrollment", "Director -Student Information", "General Counsel", "Executive Controller"]

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
        users = pandas.read_csv('newark-users.csv', engine='python')
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
            "0": ["Learner"],
            "#N/A": ["Learner"],
            "Adult Support Framework": ["Teacher Coach"],
            "CST Framework": ["Learner"],
            "Director / Supervisor": ["School Assistant Admin"],
            "Framework for Effective Teaching": ["Learner"],
            "Non-instructional": ["Learner"],
            "NPS non-Principal Leadership Framework": ["School Assistant Admin"],
            "NPS Principal Framework": ["School Admin"],
            "Nurse Framework": ["Learner"],
            "Paraprofessional": ["Learner"],
            "School-Wide Services Framework": ["Learner"],
            "Student Support Framework": ["Learner"],
            "Unaffiliated": ["Learner"]
        }

        # if the role to convert isn't a string we default them to teacher
        if not isinstance(role_to_convert, str):
            role_to_convert = "#N/A"
        whetstone_role_names = role_map[role_to_convert]
        if not whetstone_role_names:
            whetstone_role_names = ["Learner"]

        for whetstone_role_name in whetstone_role_names:
            whetstone_roles.append(ImportUtils.find_object(whetstone_role_name, 'name', roles))

        # Check User Type for one of the Department Chair job titles, if it exists the user get department chair role
        if user_type and user_type['name'] in ImportUtils.department_chair_job_titles:
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
        user_ids = list(map(lambda user: str(user["Emplid"]), users_to_import))

        def user_missing(user):
            not_multi_district = len(user['districts']) < 2
            not_archived = 'archivedAt' in user and user['archivedAt'] is None or 'archivedAt' not in user
            not_in_import = 'internalId' in user and user['internalId'] and user['internalId'] not in user_ids
            not_locked = 'locked' in user and user['locked'] is not True or 'locked' not in user
            return not_multi_district and not_archived and not_in_import and not_locked
        missing_users = list(filter(lambda user: user_missing(user), existing_users))
        for missing_user in missing_users:
            print(f'Archiving User {missing_user["name"]}')
        missing_user_ids = list(map(lambda user: user["_id"], missing_users))
        return missing_user_ids

    @staticmethod
    def get_users_to_restore(users_to_import, existing_users):
        user_ids = list(map(lambda user: str(user["Emplid"]), users_to_import))

        def user_missing(user):
            not_multi_district = len(user['districts']) < 2
            is_archived = 'archivedAt' in user and user['archivedAt'] is not None
            is_in_import = 'internalId' in user and user['internalId'] and user['internalId'] in user_ids
            not_locked = 'locked' in user and user['locked'] is not True or 'locked' not in user
            return not_multi_district and is_archived and is_in_import and not_locked
        users_to_restore = list(filter(lambda user: user_missing(user), existing_users))
        for restore_user in users_to_restore:
            print(f'Restoring User {restore_user["name"]}')
        restore_user_ids = list(map(lambda user: user["_id"], users_to_restore))
        return restore_user_ids

    @staticmethod
    def create_default_groups(school):
        if 'observationGroups' not in school:
            school['observationGroups'] = []
        group_names = list(map(lambda group: group['name'], school['observationGroups']))
        if 'Teachers' not in group_names:
            school['observationGroups'].append({
                'name': 'Teachers',
                'observers': [],
                'observees': []
            })

    @staticmethod
    def add_user_to_school_position(user, user_id, school):
        teachers_group = ImportUtils.find_object('Teachers', 'name', school['observationGroups'])
        user_role = user['Framework']
        if user_role in {'Non-instructional',  'Unaffiliated'}:
            teachers_group['observees'].append(user_id)
        if user_role == 'Adult Support Framework':
            teachers_group['observees'].append(user_id)
        if user_role in {'0', '#N/A', 'CST Framework', 'Framework for Effective Teaching', 'Paraprofessional',
                         'Nurse Framework', 'School-Wide Services', 'Student Support Framework'}:
            teachers_group['observees'].append(user_id)
        if user_role in {'NPS non-Principal Leadership Framework'}:
            school['assistantAdmins'].append(user_id)
        if user_role == 'NPS Principal Framework':
            school['admins'].append(user_id)
        if user_role == 'Director / Supervisor':
            if user['Jobcode Descr'] in ImportUtils.nps_director_job_titles:
                school['admins'].append(user_id)
            else:
                school['assistantAdmins'].append(user_id)

        # Check User Type for one of the Department Chair job titles, if it exists the user get department chair role
        if user['Jobcode Descr'] in ImportUtils.department_chair_job_titles:
            school['nonInstructionalAdmins'].append(user_id)

    @staticmethod
    def create_special_coaching_group(user, coach, school):
        group_names = list(map(lambda group: group['name'], school['observationGroups']))
        if f"{coach['name']}'s Group" not in group_names:
            school['observationGroups'].append({
                'name': f"{coach['name']}'s Group",
                'observers': [coach['_id']],
                'observees': [user['_id']]
            })
        else:
            coach_group = ImportUtils.find_object(f"{coach['name']}'s Group", 'name', school['observationGroups'])
            coach_group['observees'].append(user['_id'])

    @staticmethod
    def add_practice_user_to_school(practice_user, school):
        practice_user_id = practice_user['_id']
        teachers_group = ImportUtils.find_object('Teachers', 'name', school['observationGroups'])
        if ImportUtils.find_object(practice_user_id, 'observees', teachers_group) is None:
            teachers_group.observees.append(practice_user_id)

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
