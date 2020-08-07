from api import ImportAPI
from utils import ImportUtils

warning_messages = []


def archive_users(users_to_import, existing_users):
    print('Status: Archiving users missing from import')
    try:
        # get users who exist in Whetstone but aren't in the current import
        users_to_archive = ImportUtils.get_users_to_archive(users_to_import, existing_users)
        if len(users_to_archive):
            # archive the users who are missing from the import
            api.archive_users(users_to_archive)
    except Exception as exception:
        warning_messages.append("Error archiving users: {0}".format(exception))
        print("Error archiving users: {0}".format(exception))


def update_users(users_to_import, existing_users, schools, user_types, user_tags, roles, district):
    print('Status: Updating basic user information')
    updated_users = []
    for user_to_import in users_to_import:
        # Check that the user has an employee ID, if not we skip this user
        if user_to_import['Emplid'] is None:
            print(f'Error importing user {user_to_import["First Name"]} { user_to_import["Last Name"]}: Invalid Employee ID')
            warning_messages.append(f'Invalid Employee ID for {user_to_import["First Name"]} { user_to_import["Last Name"]}')
            continue

        # get basic user info from import
        internal_id = user_to_import['Emplid']
        email = user_to_import['Email']
        first_name = user_to_import['First Name']
        last_name = user_to_import['Last Name']
        school = ImportUtils.find_object(user_to_import['Location Descr'], 'name', schools)
        user_type = ImportUtils.find_string(user_to_import['Jobcode Descr'], user_types)
        user_tag_1 = ImportUtils.find_string(user_to_import['19-20 Rating'], user_tags['userTag1s'])
        # TODO: Add Tenure as user tag 2
        # user_tag_2 = ImportUtils.find_string(user_to_import['Tenure'], user_tags['userTag2s'])
        user_tag_3 = ImportUtils.find_string(user_to_import['Framework'], user_tags['userTag3s'])
        user_tag_4 = ImportUtils.find_string(user_to_import['Dept Descr'], user_tags['userTag4s'])

        # build user object
        user_data = {
            'first': first_name,
            'last': last_name,
            'name': first_name + ' ' + last_name,
            'internalId': internal_id,
            'email': email,
            'defaultInformation': {
                'school': school['_id'] if school is not None else None
            },
            'coach': None,
            'usertype': user_type['_id'] if user_type is not None else None,
            'districts': [district['_id']],
            'roles': ImportUtils.get_whetstone_roles(user_to_import['Framework'], roles) or [],
            'usertag1': user_tag_1,
            'usertag3': user_tag_3,
            'usertag4': user_tag_4
        }

        try:
            existing_user = ImportUtils.find_object(str(internal_id), 'internalId', existing_users)
            if existing_user is None:
                print(f'User {email} does not exist. Creating new Whetstone user')
                new_user = api.create_user(user_data)
                existing_users.append(new_user)
                updated_users.append(new_user)
            else:
                print(f'User {email} exists. Updating Whetstone user')
                updated_user = api.update_user(existing_user['_id'], user_data)
                updated_users.append(updated_user)
        except Exception as exception:
            warning_messages.append(f"Error creating/updating user [{user_data['name']}]: {exception}")
            print(f"Error creating/updating user [{user_data['name']}]: {exception}")
    return updated_users

def remove_users_from_groups(schools, locked_users):
    print('Status: Removing users from school-based groups')
    locked_user_ids = list(map(lambda user: user['_id'], locked_users))
    for school in schools:
        if 'observationGroups' in school:
            for i in range(len(school['observationGroups']) - 1, -1, -1):
                try:
                    locked_observees = ImportUtils.get_locked_group_members(school['observationGroups'][i], 'observees', locked_user_ids)
                    locked_observers = ImportUtils.get_locked_group_members(school['observationGroups'][i], 'observers', locked_user_ids)
                    if len(locked_observees) or len(locked_observers):
                        if len(locked_observees):
                            print(f'{len(locked_observers)} locked observees found in group {school["observationGroups"][i]["name"]}. Removing unlocked group members')
                            school['observationGroups'][i].observees = list(filter(lambda user: user not in locked_user_ids, school.observationGroups[i].observees))
                        if len(locked_observers):
                            print(f'{len(locked_observers)} locked observers found in group {school["observationGroups"][i]["name"]}. Removing unlocked group members')
                            school['observationGroups'][i].observers = list(filter(lambda user: user not in locked_user_ids, school.observationGroups[i].observers))
                    else:
                        print(f'No locked users found in group {school["observationGroups"][i]["name"]}. Removing group')
                        del(school['observationGroups'][i])
                except Exception as exception:
                    print("Error removing users from group: {0}".format(exception))
                    warning_messages.append(f'Error removing users from group: {school["observationGroups"][i]["name"]} at school: {school["name"]}')

            try:
                for i in range(len(school['admins']) - 1, -1, -1):
                    if school['admins'][i] not in locked_user_ids:
                        print(f'Removing admin {school["admins"][i]} from admin group at {school["name"]}')
                        del(school['admins'][i])
                for i in range(len(school['assistantAdmins']) - 1, -1, -1):
                    if school['assistantAdmins'][i] not in locked_user_ids:
                        print(f'Removing assistant admin {school["assistantAdmins"][i]} from admin group at {school["name"]}')
                        del(school['assistantAdmins'][i])
                for i in range(len(school['nonInstructionalAdmins']) - 1, -1, -1):
                    if school['nonInstructionalAdmins'][i] not in locked_user_ids:
                        print(f'Removing non-instructional admin {school["nonInstructionalAdmins"][i]} from admin group at {school["name"]}')
                        del(school['nonInstructionalAdmins'][i])
            except Exception as exception:
                print("Error removing admins from school: {0}".format(exception))
                warning_messages.append(f'Error removing admins from school: {school["name"]}')

            api.update_school(school['_id'], school)

    updated_schools = api.get_schools()
    return updated_schools


def add_users_to_groups(users_to_import, updated_users, schools):
    print("Status: Adding users to school groups")

    for school in schools:
        # Make sure the school has groups
        ImportUtils.create_default_groups(school)

    for user in users_to_import:
        try:
            user_id = user['Emplid']
            user_obj = ImportUtils.find_object(str(user_id), 'internalId', updated_users)
            user_school = ImportUtils.find_object(user['Location Descr'], 'name', schools)
            if user_school is None:
                print(f'User {user["Email"]} is missing a school or school does not exist. Skipping school position.')
                warning_messages.append(f'User {user["Email"]} is missing a school or school does not exist.')
                continue
            else:
                ImportUtils.add_user_to_school_position(user, user_obj['_id'], user_school)

            api.update_school(user_school['_id'], user_school)
        except Exception as exception:
            print("Error adding user to school position: {0}".format(exception))
            warning_messages.append(f'Error adding user {user["Email"]} to school position')


def complete_import():
    if len(warning_messages):
        messages = ["<p>There was a successful import but the following events occurred:</p><ul>"]
        for message in warning_messages:
            messages.append(f'<li>{message}</li>')
        messages.append('</ul>')
    else:
        messages = ['<p>The user import completed successfully.</p>']
    email_content = ImportUtils.get_email_message(''.join(messages))
    send_email(email_content)


def send_email(body):
    email_recipients = ['kevin@whetstoneeducation.org']
    for recipient in email_recipients:
        payload = {
            'to': recipient,
            'from': 'support@whetstoneeducation.org',
            'subject': '[Whetstone] User Import Status',
            'content': body
        }
        api.send_email(payload)


try:
    # instantiate API class
    api = ImportAPI()

    # get district
    district = api.get_district('newark-school-district')
    api.district = district['_id']

    # get all district schools
    schools = api.get_schools()

    # get all district user types
    user_types = api.get_user_types()

    # get all district user tags
    user_tags = api.get_user_tags()

    # get all existing users
    existing_users = api.get_all_users()

    # get all locked users
    locked_users = api.get_locked_users()

    # get all district roles
    roles = api.get_district_roles()

    # parse the csv file containing users to import
    users_to_import = ImportUtils.get_csv_users(locked_users)

    # archive users
    archive_users(users_to_import, existing_users)

    # add / update users in import
    updated_users = update_users(users_to_import, existing_users, schools, user_types, user_tags, roles, district)

    # remove users from school groups
    schools = remove_users_from_groups(schools, locked_users)

    # add users to school groups
    add_users_to_groups(users_to_import, updated_users, schools)

    # complete the import by sending an email
    complete_import()

except Exception as e:
    print("Error: {0}".format(e))
    warning_messages.append("Error: {0}".format(e))
    email_body = ImportUtils.get_email_message("An error occurred while importing users")
    send_email(email_body)

