import argparse
import datetime
import logging
import os
import random
import shelve
import time
import uuid
import yaml

from typing import List

import coloredlogs
import requests
import schedule

from src.config import Config

coloredlogs.install(level="INFO")
log = logging.getLogger("main")

APP_VERSION = "4.19.0"
CUSTOM_USER_AGENT = f"Patient Portal; {APP_VERSION}; {str(uuid.uuid4())}; Android; {str(random.randint(23, 29))}; {str(uuid.uuid4())}"


class LuxMedSniper:
    LUXMED_TOKEN_URL = 'https://portalpacjenta.luxmed.pl/PatientPortalMobileAPI/api/token'
    LUXMED_LOGIN_URL = 'https://portalpacjenta.luxmed.pl/PatientPortal/Account/LogInToApp'
    NEW_PORTAL_RESERVATION_URL = 'https://portalpacjenta.luxmed.pl/PatientPortal/NewPortal/terms/index'

    def __init__(self, configuration_file="luxmedSniper.yaml"):
        self.log = logging.getLogger("LuxMedSniper")
        self.log.info("LuxMedSniper logger initialized")
        self._loadConfiguration(configuration_file)
        self._setup_providers()
        self._createSession()
        self._get_access_token()
        self._logIn()

    def _get_access_token(self) -> str:

        authentication_body = {
            'username': self.config.luxmed.email,
            'password': self.config.luxmed.password,
            "grant_type": "password",
            "account_id": str(uuid.uuid4())[:35],
            "client_id": str(uuid.uuid4())
        }

        response = self.session.post(LuxMedSniper.LUXMED_TOKEN_URL,
                                     data=authentication_body)
        content = response.json()
        self.access_token = content['access_token']
        self.refresh_token = content['refresh_token']
        self.token_type = content['token_type']
        self.session.headers.update({'Authorization': self.access_token})
        self.log.info('Successfully received an access token!')

        return response.json()["access_token"]

    def _createSession(self):
        self.session = requests.Session()
        self.session.headers.update({'Host': 'portalpacjenta.luxmed.pl'})
        self.session.headers.update({'Origin': "https://portalpacjenta.luxmed.pl"})
        self.session.headers.update({'Content-Type': "application/x-www-form-urlencoded"})
        self.session.headers.update({'x-api-client-identifier': 'iPhone'})
        self.session.headers.update({'Accept': 'application/json, text/plain, */*'})
        self.session.headers.update({'Custom-User-Agent': CUSTOM_USER_AGENT})
        self.session.headers.update({'User-Agent': 'okhttp/3.11.0'})
        self.session.headers.update({'Accept-Language': 'en;q=1.0, en-PL;q=0.9, pl-PL;q=0.8, ru-PL;q=0.7, uk-PL;q=0.6'})
        self.session.headers.update({'Accept-Encoding': 'gzip;q=1.0, compress;q=0.5'})

    def _loadConfiguration(self, configuration_file):
        try:
            config_data = open(os.path.expanduser(configuration_file), 'r').read()
        except IOError:
            raise Exception(
                'Cannot open configuration file ({file})!'.format(file=configuration_file))
        try:
            loaded_config = yaml.load(config_data, Loader=yaml.FullLoader)
            self.config = Config(**loaded_config)
        except Exception as yaml_error:
            raise Exception('Configuration problem: {error}'.format(error=yaml_error))

    def _logIn(self):

        params = {
            "app": "search",
            "client": 3,
            "paymentSupported": "true",
            "lang": "pl"
        }
        response = self.session.get(LuxMedSniper.LUXMED_LOGIN_URL, params=params)

        if response.status_code != 200:
            raise LuxmedSniperException("Unexpected response code, cannot log in")

        self.log.info('Successfully logged in!')

    def _parseVisitsNewPortal(self, data) -> List[dict]:
        appointments = []
        (clinicIds, doctorIds) = self.config.luxmedsniper.doctor_locator_id.strip().split('*')[-2:]

        excluded_facilities = self.config.luxmedsniper.excluded_facilities
        content = data.json()
        for termForDay in content["termsForService"]["termsForDays"]:
            for term in termForDay["terms"]:
                doctor = term['doctor']
                clinic_name: str = term['clinic']

                if doctorIds != '-1' and str(doctor['id']) != doctorIds:
                    continue
                if clinicIds != '-1' and str(term['clinicId']) != clinicIds:
                    continue
                if any([excluded_facility in clinic_name for excluded_facility in excluded_facilities]):
                    continue

                appointments.append(
                    {
                        'AppointmentDate': term['dateTimeFrom'],
                        'ClinicId': term['clinicId'],
                        'ClinicPublicName': clinic_name,
                        'DoctorName': f'{doctor["academicTitle"]} {doctor["firstName"]} {doctor["lastName"]}',
                        'ServiceId': term['serviceId']
                    }
                )
        return appointments

    def _getAppointmentsNewPortal(self):
        try:
            (cityId, serviceId, clinicIds, doctorIds) = self.config.luxmedsniper.doctor_locator_id.strip().split('*')
        except ValueError:
            raise Exception('DoctorLocatorID seems to be in invalid format')
        date_to = (datetime.date.today() + datetime.timedelta(days=self.config.luxmedsniper.lookup_time_days))
        params = {
            "cityId": cityId,
            "serviceVariantId": serviceId,
            "languageId": 10,
            "searchDateFrom": datetime.date.today().strftime("%Y-%m-%d"),
            "searchDateTo": date_to.strftime("%Y-%m-%d"),
        }
        if clinicIds != '-1':
            params['facilitiesIds'] = clinicIds.split(',')
        if doctorIds != '-1':
            params['doctorsIds'] = doctorIds.split(',')

        response = self.session.get(LuxMedSniper.NEW_PORTAL_RESERVATION_URL, params=params)
        return [*filter(
            lambda a: datetime.datetime.fromisoformat(a['AppointmentDate']).date() <= date_to,
            self._parseVisitsNewPortal(response))]

    def check(self):
        appointments = self._getAppointmentsNewPortal()
        if not appointments:
            self.log.info("No appointments found.")
            return
        for appointment in appointments:
            self.log.info(
                "Appointment: {AppointmentDate}, {ClinicPublicName}, {DoctorName}".format(
                    **self._format_appointment(appointment)))
            if not self._isAlreadyKnown(appointment):
                self._addToDatabase(appointment)
                self._send_notification(appointment)
                self.log.info(
                    "Notification sent: {AppointmentDate}, {ClinicPublicName}, {DoctorName}".format(
                        **self._format_appointment(appointment)))
            else:
                self.log.debug('Notification was already sent.')

    def _addToDatabase(self, appointment):
        db = shelve.open(self.config.misc.notifydb)
        notifications = db.get(appointment['DoctorName'], [])
        notifications.append(appointment['AppointmentDate'])
        db[appointment['DoctorName']] = notifications
        db.close()

    def _send_notification(self, appointment):
        appointment = self._format_appointment(appointment)
        for provider in self.notification_providers:
            provider(appointment)

    def _format_appointment(self, appointment):
        appointment = appointment.copy()
        date_format = self.config.misc.date_format
        appointment['AppointmentDate'] = datetime.datetime.fromisoformat(
            appointment['AppointmentDate']).strftime(date_format)
        return appointment

    def _isAlreadyKnown(self, appointment):
        db = shelve.open(self.config.misc.notifydb)
        notifications = db.get(appointment['DoctorName'], [])
        db.close()
        if appointment['AppointmentDate'] in notifications:
            return True
        return False

    def _setup_providers(self):
        self.notification_providers = []
        chosen_providers = self.config.luxmedsniper.notification_provider

        if "pushover" in chosen_providers:
            from src.pushover_client import PushoverClient
            config = self.config.pushover
            pushover_client = PushoverClient(config.user_key, config.api_token)
            self.notification_providers.append(lambda appointment: pushover_client.send_message(
                config.message_template.format(**appointment, title=config.title)))
        if "slack" in chosen_providers:
            from slack_sdk import WebClient
            config = self.config.slack
            client = WebClient(token=config.api_token)
            channel = config.channel
            self.notification_providers.append(
                lambda appointment: client.chat_postMessage(channel=channel,
                                                            text=config.message_template.format(**appointment))
            )
        if "pushbullet" in chosen_providers:
            from pushbullet import Pushbullet
            config = self.config.pushbullet
            pb = Pushbullet(config.access_token)
            self.notification_providers.append(
                lambda appointment: pb.push_note(title=config.title,
                                                 body=config.message_template.format(**appointment)))


def work(config):
    try:
        luxmed_sniper = LuxMedSniper(configuration_file=config)
        luxmed_sniper.check()
    except Exception as s:
        log.error(s)


class LuxmedSniperException(Exception):
    pass


if __name__ == "__main__":
    log.info("LuxMedSniper - Lux Med Appointment Sniper")
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-c", "--config",
        help="Configuration file path", default="luxmedSniper.yaml"
    )
    parser.add_argument(
        "-d", "--delay",
        type=int, help="Delay in fetching updates [s]", default=1800
    )
    args = parser.parse_args()
    work(args.config)
    schedule.every(args.delay).seconds.do(work, args.config)
    while True:
        schedule.run_pending()
        time.sleep(1)
