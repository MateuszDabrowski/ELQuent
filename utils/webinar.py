#!/usr/bin/env python3.6
# -*- coding: utf8 -*-

'''
ELQuent.webinar
Gets attendees and registered users from ClickMeeting
and uploads them to Oracle Eloqua as shared list

Mateusz Dąbrowski
github.com/MateuszDabrowski
linkedin.com/in/mateusz-dabrowski-marketing/
'''

# Python imports
import os
import sys
import json
import pickle
import datetime
import pyperclip
from colorama import Fore, init

# ELQuent imports
import utils.api.api as api

# Initialize colorama
init(autoreset=True)

# Globals
naming = None
click_key = None
click_root = None
source_country = None

# Predefined messege elements
ERROR = f'{Fore.WHITE}[{Fore.RED}ERROR{Fore.WHITE}] {Fore.YELLOW}'
SUCCESS = f'{Fore.WHITE}[{Fore.GREEN}SUCCESS{Fore.WHITE}] '


def country_naming_setter(country):
    '''
    Sets source_country for all functions
    Loads json file with naming convention
    '''
    global source_country
    source_country = country

    # Creates globals related to Click API
    global click_key
    click_key = get_click_auth()
    global click_root
    click_root = 'https://api.clickmeeting.com/v1/'

    # Loads json file with naming convention
    with open(file('naming'), 'r', encoding='utf-8') as f:
        global naming
        naming = json.load(f)


'''
=================================================================================
                            File Path Getter
=================================================================================
'''


def file(file_path):
    '''
    Returns file path to template files
    '''

    def find_data_file(filename, directory='templates'):
        '''
        Returns correct file path for both script and frozen app
        '''
        if directory == 'templates':  # For reading template files
            if getattr(sys, 'frozen', False):
                datadir = os.path.dirname(sys.executable)
            else:
                datadir = os.path.dirname(os.path.dirname(__file__))
            return os.path.join(datadir, 'utils', directory, filename)
        elif directory == 'api':  # For writing auth files
            if getattr(sys, 'frozen', False):
                datadir = os.path.dirname(sys.executable)
            else:
                datadir = os.path.dirname(os.path.dirname(__file__))
            return os.path.join(datadir, 'utils', directory, filename)

    file_paths = {
        'naming': find_data_file('naming.json', directory='api'),
        'click': find_data_file('click.p', directory='api')
    }

    return file_paths.get(file_path)


'''
=================================================================================
                                Click Authentication
=================================================================================
'''


def get_click_auth():
    '''
    Returns ClickMeeting API Key needed for authorization
    '''
    if not os.path.isfile(file('click')):
        while True:
            print(
                f'\n{Fore.WHITE}Write or copypaste ClickMeeting API Key and click [Enter]')
            click_api_key = input(' ')
            if not click_api_key:
                click_api_key = pyperclip.paste()
            if len(click_api_key) == 42:
                break
            else:
                print(f'{ERROR}Incorrect API Key!')
        pickle.dump(click_api_key, open(file('click'), 'wb'))
    click_api_key = pickle.load(open(file('click'), 'rb'))

    return click_api_key


'''
=================================================================================
                        ClickMeeting API specific functions
=================================================================================
'''


def click_export_rooms(export_time_range):
    '''
    Returns tuples of active and inactive ClickMeeting rooms with ID and name
    '''

    # Save active rooms
    active_ids = []
    active_names = []
    root = click_root + 'conferences/active'
    response = api.api_request(root, api='click')
    rooms_active_click = response.json()
    for room in rooms_active_click:
        active_ids.append(room['id'])
        active_names.append(room['name'])
    active_rooms = list(zip(active_ids, active_names))

    # Save inactive rooms
    inactive_ids = []
    inactive_names = []
    root = click_root + 'conferences/inactive'
    response = api.api_request(root, api='click')
    rooms_inactive_click = response.json()
    for room in rooms_inactive_click:
        # Creating datetime version of room end date
        room_date = room['ends_at'][:10] + ' ' + room['ends_at'][11:16]
        room_datetime = datetime.datetime.strptime(room_date, '%Y-%m-%d %H:%M')
        # Exporting room only if end date withing export date time
        if (datetime.datetime.today() - room_datetime).days <= export_time_range:
            inactive_ids.append(room['id'])
            inactive_names.append(room['name'])
    inactive_rooms = list(zip(inactive_ids, inactive_names))

# <Company specific code> =========================================================================
    # Filter out internal webinars from export
    internal_webinars = naming[source_country]['webinar']['filters']
    for filtering in internal_webinars:
        active_rooms = [(id, name) for (id, name)
                        in active_rooms if f'{filtering}' not in name.lower()]
        inactive_rooms = [(id, name) for (id, name)
                          in inactive_rooms if f'{filtering}' not in name.lower()]
# ========================================================================= </Company specific code>

    return (active_rooms, inactive_rooms)


def click_export_sessions(click_rooms):
    '''
    Returns ClickMeeting sessions for active and inactive rooms
    '''

    click_sessions = {}

    # Save all sessions
    for room in click_rooms:
        root = f'{click_root}conferences/{room[0]}/sessions'
        response = api.api_request(root, api='click')
        if response.status_code == 200:
            print(f'{Fore.GREEN}|', end='', flush=True)
            sessions_in_room = response.json()
            for session in sessions_in_room:
                click_session = (session['id'], session['end_date'][: 10]
                                 + ' ' + session['end_date'][11:16])
                click_sessions[click_session] = room
        else:
            print(f'{Fore.RED}|', end='', flush=True)
    print()
    return click_sessions


def click_export_registered(active_rooms):
    '''
    Returns ClickMeeting room registrations within chosen time range
    '''

    sessions_to_import = {}

    # Calls registrations API only if room has active registration
    for room in active_rooms:
        room_id = room[0]
        room_name = room[1]
        root = f'{click_root}conferences/{room_id}/registrations/all'
        response = api.api_request(root, api='click')
        if response.status_code == 200:
            print(f'{Fore.GREEN}|', end='', flush=True)
            registered = response.json()

            if response:
                # Create list of registered
                registered_list = []
                for user in registered:
                    if user['fields']['Email Address'] is not None:
                        registered_list.append(user['fields']['Email Address'])

                # Deduplicating list of email addresses
                registered_list = list(set(registered_list))

                # Filter out corporate and spam e-mails
                registered_list = [user for user in registered_list if
                                   '@wolterskluwer.' not in user.lower() and len(user) > 8]

                # Modifying values for Eloqua naming convention
                room_name = room_name\
                    .replace(',', '')\
                    .replace('!', '')\
                    .replace('-', '')\
                    .replace('.', '')\
                    .replace(':', '')\
                    .replace('?', '')\
                    .replace('–', '')\
                    .replace(' ', '-')
                room_name = room_name[:26] + '-' if len(room_name) > 26 \
                    else room_name + '-'
                if 'Progman' in room_name:
                    psp_name = naming[source_country]['webinar']['progman_psp']
                else:
                    psp_name = naming[source_country]['webinar']['webinar_psp']

                # Naming convention for shared list of uploaded registered users
                shared_list_name = naming[source_country]['webinar']['name'] + \
                    room_name + psp_name + '_zarejestrowani'
                while '--' in shared_list_name:
                    shared_list_name = shared_list_name.replace('--', '-')

                # Create dict with name and email list
                sessions_to_import[shared_list_name] = registered_list
        else:
            print(f'{Fore.RED}|', end='', flush=True)

    # Cleans pairs with empty value from import
    sessions_to_import = {
        k: v for (k, v) in sessions_to_import.items() if len(v) != 0}
    print()
    for name, mails in sessions_to_import.items():
        print(
            f'{Fore.WHITE}[{Fore.YELLOW}{len(mails)}{Fore.WHITE}] {name}')

    return sessions_to_import  # {'listName': ['mail', 'mail']}


def click_export_attendees(click_sessions, export_time_range):
    '''
    Returns ClickMeeting attendees from sessions within chosen time range
    '''

    sessions_to_import = {}

    # Create list of attendees of each session in chosen period
    for key, value in click_sessions.items():
        # click_sessions unpacking
        session_id, session_date = key
        room_id, room_name = value

        # Creating datetime version of session_date for EXPORT_TIME_RANGE
        session_datetime = datetime.datetime.strptime(
            session_date, '%Y-%m-%d %H:%M')

        # Calls attendees API only if session within given time range
        if (datetime.datetime.today() - session_datetime).days <= export_time_range:
            root = f'{click_root}conferences/{room_id}/sessions/{session_id}/attendees'
            response = api.api_request(
                root, api='click')
            attendees = response.json()

            # Create list of attendees
            attendees_list = []
            for attendee in attendees:
                if attendee['role'] == 'listener' and attendee['email'] is not None:
                    attendees_list.append(attendee['email'])

            # Deduplicating list of email addresses
            attendees_list = list(set(attendees_list))

            # Filter out corporate and spam e-mails
            attendees_list = [att for att in attendees_list if
                              '@wolterskluwer.' not in att.lower() and len(att) > 8]

            # Modifying values for Eloqua naming convention
            room_name = room_name\
                .replace(',', '')\
                .replace('!', '')\
                .replace('-', '')\
                .replace('.', '')\
                .replace(':', '')\
                .replace('?', '')\
                .replace('–', '')\
                .replace(' ', '-')
            room_name = room_name[:29] + '-' if len(room_name) > 29 \
                else room_name + '-'
            session_date = f'{session_date[8:10]}-{session_date[5:7]}-{session_date[2:4]}-'
            if 'Progman' in room_name:
                psp_name = naming[source_country]['webinar']['progman_psp']
            else:
                psp_name = naming[source_country]['webinar']['webinar_psp']

            # Naming convention for shared list of uploaded attendees
            shared_list_name = naming[source_country]['webinar']['name'] + str(session_id) + '-' + room_name + \
                session_date + psp_name + '_uczestnicy'
            while '--' in shared_list_name:
                shared_list_name = shared_list_name.replace('--', '-')

            # Create dict with name and email list
            sessions_to_import[shared_list_name] = attendees_list

    # Cleans pairs with empty value from import
    sessions_to_import = {
        k: v for (k, v) in sessions_to_import.items() if len(v) != 0}
    for name, mails in sessions_to_import.items():
        print(
            f'{Fore.WHITE}[{Fore.YELLOW}{len(mails)}{Fore.WHITE}] {name}')

    return sessions_to_import  # {'listName': ['mail', 'mail']}


'''
=================================================================================
                        Attendees to Shared List flow
=================================================================================
'''


def click_to_elq():
    '''
    Gets attendees and users registered to ClickMeeting webinars
    and uploads them to Eloqua as a shared list
    '''

    # Gets export timeframe from user
    while True:
        print(
            f'\n{Fore.WHITE}» [{Fore.YELLOW}TIMEFRAME{Fore.WHITE}] Enter number of days to export:', end='')
        export_time_range = input(' ')
        try:
            export_time_range = int(export_time_range)
        except ValueError:
            print(
                f'\t{ERROR}Please enter numeric value!')
            continue
        else:
            break

    # Function pipe
    print(f'\n{Fore.YELLOW}» Getting rooms from chosen timeframe')
    active_rooms, inactive_rooms = click_export_rooms(export_time_range)
    print(f'{Fore.GREEN}» Imported {len(active_rooms)} active and {len(inactive_rooms)} inactive rooms')
    click_rooms = active_rooms + inactive_rooms
    print(f'\n{Fore.YELLOW}» Getting sessions')
    click_sessions = click_export_sessions(click_rooms)
    print(f'{Fore.GREEN}» Imported {len(click_sessions)} sessions')
    print(f'\n{Fore.YELLOW}» Getting registered users in active rooms')
    click_registered_export = click_export_registered(active_rooms)
    print(f'{Fore.GREEN}» Imported registed users from {len(click_registered_export)} webinars')
    print(f'\n{Fore.YELLOW}» Getting attendees from chosen timeframe')
    click_attendee_export = click_export_attendees(
        click_sessions, export_time_range)
    print(f'{Fore.GREEN}» Imported attendees from {len(click_attendee_export)} webinars')
    click_exports = {**click_registered_export, **click_attendee_export}
    api.upload_contacts(click_exports, list_type='webinar', choice='append')

    return


'''
=================================================================================
                            Attendees to CDO flow
=================================================================================
'''


def click_to_activity(last_webinar_sync):
    '''
    Gets ClickMeeting webinars attendees
    uploads them to Eloqua as a shared list
    and adds them to External Activity
    '''

    # Parse last_webinar_sync from string to datetime
    last_sync = datetime.datetime.strptime(last_webinar_sync, '%Y-%m-%d %H:%M')

    # Gets current datetime to update last_webinar_sync shared list
    current_sync = datetime.datetime.today().strftime('%Y-%m-%d %H:%M')

    # Gets list of already uploaded webinars
    uploaded_sessions_shared_list = api.eloqua_asset_get(
        naming[source_country]['id']['uploaded_sessions_list'], 'sharedContent', depth='complete')
    old_sessions_shared_list = uploaded_sessions_shared_list['contentHtml']
    old_sessions_shared_list = old_sessions_shared_list.split(',')

    '''
    =================================================== Get room data
    '''

    print(f'\n{Fore.YELLOW}» Getting rooms from chosen timeframe')
    # Save active rooms
    active_ids = []
    active_names = []
    root = click_root + 'conferences/active'
    response = api.api_request(root, api='click')
    rooms_active_click = response.json()
    for room in rooms_active_click:
        active_ids.append(room['id'])
        active_names.append(room['name'])
    active_rooms = list(zip(active_ids, active_names))

    # Save inactive rooms
    inactive_ids = []
    inactive_names = []
    root = click_root + 'conferences/inactive'
    response = api.api_request(root, api='click')
    rooms_inactive_click = response.json()
    for room in rooms_inactive_click:
        # Creating datetime version of room end date
        room_date = room['ends_at'][:10] + ' ' + room['ends_at'][11:16]
        room_datetime = datetime.datetime.strptime(room_date, '%Y-%m-%d %H:%M')
        # Skip rooms older then last sync
        if room_datetime <= last_sync:
            inactive_ids.append(room['id'])
            inactive_names.append(room['name'])
    inactive_rooms = list(zip(inactive_ids, inactive_names))
    print(f'{Fore.GREEN}» Imported {len(active_rooms)} active and {len(inactive_rooms)} inactive rooms')

    click_rooms = active_rooms + inactive_rooms

    '''
    =================================================== Get session data
    '''

    print(f'\n{Fore.YELLOW}» Getting sessions')
    click_sessions = {}
    # Save all sessions
    for room in click_rooms:
        root = f'{click_root}conferences/{room[0]}/sessions'
        response = api.api_request(root, api='click')
        if response.status_code == 200:
            print(f'{Fore.GREEN}|', end='', flush=True)
            sessions_in_room = response.json()
            for session in sessions_in_room:
                # Skip already uploaded sessions
                if session['id'] not in old_sessions_shared_list:
                    click_session = (
                        session['id'],
                        session['start_date'][:10] + ' ' +
                        session['start_date'][11:16],
                        session['end_date'][:10] + ' ' +
                        session['end_date'][11:16]
                    )
                    click_sessions[click_session] = room
        else:
            print(f'{Fore.RED}|', end='', flush=True)
    print(f'\n{Fore.GREEN}» Imported {len(click_sessions)} sessions')

    '''
    =================================================== Get attendees data
    '''

    print(f'\n{Fore.YELLOW}» Getting attendees')
    attendees = []
    activites = []
    new_sessions_shared_list = []
    # Create list of attendees of each session in chosen period
    for key, value in click_sessions.items():
        # click_sessions unpacking
        session_id, session_start_date, session_end_date = key
        room_id, room_name = value

        # Creating datetime version of session_date for EXPORT_TIME_RANGE
        session_end_datetime = datetime.datetime.strptime(
            session_end_date, '%Y-%m-%d %H:%M')

        # Skip already sessions older then last sync
        if session_end_datetime <= last_sync:
            root = f'{click_root}conferences/{room_id}/sessions/{session_id}/attendees'
            response = api.api_request(
                root, api='click')
            attendees = response.json()

            # Create list of attendees
            attendees_list = []
            for attendee in attendees:
                if attendee['role'] == 'listener' and attendee['email'] is not None:
                    attendees_list.append(attendee['email'])

            # Deduplicating list of email addresses
            attendees_list = list(set(attendees_list))

            # Filter out corporate and spam e-mails
            attendees_list = [att for att in attendees_list if
                              '@wolterskluwer.' not in att.lower() and len(att) > 8]

            # Modifying values for Eloqua naming convention
            room_name = room_name\
                .replace(',', '')\
                .replace('!', '')\
                .replace('-', '')\
                .replace('.', '')\
                .replace(':', '')\
                .replace('?', '')\
                .replace('–', '')\
                .replace(' ', '-')
            room_name = room_name[:40] + '-' if len(room_name) > 40 \
                else room_name + '-'
            session_date = f'{session_date[2:4]}-{session_date[5:7]}-{session_date[8:10]}'

            # Naming convention for shared list of uploaded attendees
            activity_name = f'WK{source_country}_{session_date}_{str(session_id)}-{room_name}_webinar'
            while '--' in activity_name:
                activity_name = activity_name.replace('--', '-')

            # Build external activity structured list
            campaign_id = naming[source_country]['id']['campaign']['External_Activity']
            for attendee in attendees_list:
                # [E-mail, CampaignId, AssetName, AssetType, AssetDate, ActivityType]
                activites.append([
                    attendee, campaign_id,
                    activity_name, 'Webinar',
                    session_start_date, 'Attended'
                ])

            # Update shared content with newly uploaded session_ids
            new_sessions_shared_list.append(session_id)
    print(f'{Fore.GREEN}» Imported {len(attendees_list)} attendees from {len(activites)} sessions')

    '''
    =================================================== Upload contacts & activites
    '''

    api.eloqua_create_webinar_activity(attendees_list, activites)

    '''
    =================================================== Update list of uploaded sessions
    '''

    print(f'\n{Fore.YELLOW}» Saving list of all uploaded webinar sessions')
    # Creates a string with id's of all uploaded webinar sessions
    all_sessions_shared_list = (',').join(
        old_sessions_shared_list + new_sessions_shared_list)

    # Build shared content data for updating the list of uploaded sessions
    data = {
        'id': uploaded_sessions_shared_list.get('id'),
        'name': uploaded_sessions_shared_list.get('name'),
        'contentHTML': all_sessions_shared_list
    }

    # Updating list of uploaded sessions to shared content
    api.eloqua_put_sharedcontent(
        naming[source_country]['id']['uploaded_sessions_list'], data=data)

    '''
    =================================================== Update last sync date
    '''

    print(f'\n{Fore.YELLOW}» Saving last sync date')
    # Gets date of last webinar sync
    last_webinar_sync = api.eloqua_asset_get(
        naming[source_country]['id']['webinar_sync'], 'sharedContent', depth='complete')

    # Build shared content data for updating the last sync date
    data = {
        'id': last_webinar_sync.get('id'),
        'name': last_webinar_sync.get('name'),
        'contentHTML': current_sync
    }

    # Updating last sync date to shared content
    api.eloqua_put_sharedcontent(
        naming[source_country]['id']['webinar_sync'], data=data)

    print(f'\n{SUCCESS}External Activities uploaded to Eloqua!')

    return


'''
=================================================================================
                            Webinar module menu
=================================================================================
'''


def webinar_module(country):
    '''
    Lets user choose which webinar module utility he wants to use
    '''
    # Create global source_country and load json file with naming convention
    country_naming_setter(country)

    # Gets date of last webinar sync
    last_webinar_sync = api.eloqua_asset_get(
        naming[source_country]['id']['webinar_sync'], 'sharedContent', depth='complete')
    last_webinar_sync = last_webinar_sync['contentHtml']
    print(
        f'\n{Fore.WHITE}Last webinar sync was made on {Fore.YELLOW}{last_webinar_sync}')

    # Campaign type chooser
    print(
        f'\n{Fore.GREEN}ELQuent.webinar Utilites:'
        f'\n{Fore.WHITE}[{Fore.YELLOW}1{Fore.WHITE}]\t» [{Fore.YELLOW}Activities{Fore.WHITE}] Uploads webinar attendees to Eloqua'
        f'\n{Fore.WHITE}[{Fore.YELLOW}2{Fore.WHITE}]\t» [{Fore.YELLOW}Contacts{Fore.WHITE}] Uploads webinar attendees to Eloqua {Fore.YELLOW}(Legacy)'
        f'\n{Fore.WHITE}[{Fore.YELLOW}Q{Fore.WHITE}]\t» [{Fore.YELLOW}Quit to main menu{Fore.WHITE}]'
    )
    while True:
        print(f'{Fore.YELLOW}Enter number associated with chosen utility:', end='')
        choice = input(' ')
        if choice.lower() == 'q':
            break
        elif choice == '1':
            click_to_activity(last_webinar_sync)
            break
        elif choice == '2':
            click_to_elq()
            break
        else:
            print(f'{Fore.RED}Entered value does not belong to any utility!')
            choice = ''

    return
