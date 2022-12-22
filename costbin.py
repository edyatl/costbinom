#!/usr/bin/env python3
"""
    Developed by @edyatl <edyatl@yandex.ru> December 2022
    https://github.com/edyatl

"""
import time
import re
import requests
import datetime
import pytz

import logging
import sqlite3 as sql
from config import Configuration as cfg
import sys
import getopt

__version__ = '0.1.0'

def get_cls_logger(cls: str) -> object:
    """
    Logger config. Sets handler to a file, formater and logging level.

    :param cls:
        str Name of class where logger calling.
    :return:
        Returns Logger instans.
    """
    logger = logging.getLogger(cls)
    if not logger.handlers:
        handler = logging.FileHandler(cfg.LOG_FILE)
        formatter = logging.Formatter(
            "%(asctime)s %(name)-16s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if cfg.DEBUG else logging.INFO)
    return logger


class BaseConnect:
    BASE_URL = "https://"
    logger = get_cls_logger(__qualname__)

    def __init__(self, **kwargs):
        """
        Constructor func, gets auth token and makes an instance.
        Trying to connect db or creating it if not exists.
        """
        self.token = kwargs.get("token") or ""
        self.base_url = self.BASE_URL
        self.logger.debug("Make an instance of %s class", self.__class__.__name__)

        with sql.connect(cfg.DB_FILE, timeout=10) as con:
            db = con.cursor()

            try:
                self.logger.debug("Try to connect sqlite db")
                db.execute("select id from binom")
            except sql.OperationalError:
                self.logger.debug("Sqlite db not exists, creating it from schema")
                db.executescript(open(cfg.SCHEMA_FILE, "rt", encoding="utf-8").read())

    def requests_call(self, verb: str, url: str, **kwargs) -> tuple:
        """
        Wraping func for requests with errors handling.

        :param verb:
            str Method of request ``get`` or ``post``.
        :param url:
            str URL to connect.
        :return:
            Returns a tuple of response object and error.
            If an error occurs, the response will be empty
            and vice versa otherwise.
        """
        r: object = None
        error: str = None
        retries: int = 10
        delay: int = 6

        for retry in range(retries):
            try:
                self.logger.info("Try %s request %s", verb, url)
                r = requests.request(verb, url, **kwargs)  # (url, timeout=3)
                r.raise_for_status()
                self.logger.info(
                    "Get answer with status code: %s %s", r.status_code, r.reason
                )
                return r, error
            except requests.exceptions.HTTPError as errh:
                self.logger.error("Http Error: %s", errh)
                error = errh
                self.logger.info(
                    "Don't give up! Trying to reconnect, retry %s of %s",
                    retry + 1,
                    retries,
                )
                time.sleep(delay)
            except requests.exceptions.ConnectionError as errc:
                self.logger.error("Connection Error: %s", errc)
                error = errc
                self.logger.info(
                    "Don't give up! Trying to reconnect, retry %s of %s",
                    retry + 1,
                    retries,
                )
                time.sleep(delay)
            except requests.exceptions.Timeout as errt:
                self.logger.error("Timeout Error: %s", errt)
                error = errt
                self.logger.info(
                    "Don't give up! Trying to reconnect, retry %s of %s",
                    retry + 1,
                    retries,
                )
                time.sleep(delay)
            except requests.exceptions.RequestException as err:
                self.logger.error("OOps: Unexpected Error: %s", err)
                error = err
                self.logger.info(
                    "Don't give up! Trying to reconnect, retry %s of %s",
                    retry + 1,
                    retries,
                )
                time.sleep(delay)

        return r, error

    def save_costs_to_cache_db(
        self,
        binom_id: int,
        date_s: str,
        date_e: str,
        timezone: int,
        token_val: int,
        cost: float,
    ):
        """
        Saves data from the ads source to a local db.
        Before inserting, it checks if the record is already in the db
        to prevent duplication.

        :param binom_id:
            int Digits extracted from the campaign name string.
        :param date_s:
            str Date of start point in format ``YYYY-mm-dd``.
        :param date_e:
            str Date of end point in format  ``YYYY-mm-dd``.
        :param timezone:
            int Time zone offset from UTC.
        :param token_val:
            int Identificator of placement or zone.
        :param cost:
            float Total cost of placement or zone.
        """
        payload = {
            "date": datetime.date.today(),
            "source": self.__class__.__name__,
            "binom_id": binom_id,
            "date_s": date_s,
            "date_e": date_e,
            "timezone": timezone,
            "token_val": token_val,
            "cost": cost,
        }
        with sql.connect(cfg.DB_FILE, timeout=10) as con:
            db = con.cursor()

            db.execute(
                "select id from binom where date=? and source=? and binom_id=? and date_s=?"
                "and date_e=? and timezone=? and token_val=? and cost=?",
                (*payload.values(),),
            )
            if len(db.fetchall()) == 0:
                db.execute(
                    "insert into binom (date,source,binom_id,date_s,date_e,timezone,token_val,cost)"
                    "values (?,?,?,?,?,?,?,?)",
                    (*payload.values(),),
                )
                try:
                    con.commit()
                    self.logger.info("New %s record inserted in db", payload["source"])
                except sql.OperationalError as err:
                    self.logger.error("OOps: Operational Error: %s", err)
                    return
            else:
                self.logger.warning("Record has already in db, skipping")

    @staticmethod
    def extract_binom_id(name: str, patterns: list) -> int:
        """
        Generates a binom_id from the given string,
        extracts digits using regular expressions.

        :param name:
            str from alias atrib.
        :param patterns:
            list of regexps for binom_id matching.
        :return:
            Returns digits or ``None``.
        """

        for ptr in patterns:
            m = re.search(ptr, name)
            if m is not None:
                return int(m.group(1))
        return


class Adsterra(BaseConnect):
    TIMEZONE_NAME = "UTC"
    TIMEZONE = pytz.timezone(TIMEZONE_NAME)
    TIMEZONE_OFFSET = (
        int(datetime.datetime.utcnow().astimezone(TIMEZONE).strftime("%z")) // 100
    )
    BASE_URL = cfg.ADSTERRA_BASE_URL
    PATTERNS = [
            r"^(\d+).*",
            r"t(\d+).*",
            r"old-(\d+).*",
            r"(\d+).*",
        ]
    logger = get_cls_logger(__qualname__)

    def get_campaigns(self) -> list:
        """
        Makes request to Adsterra's API and gets campaigns list.
        Generates binom_id for every item from an alias.

        :return:
            Returns campaigns list of dicts sorted by id.
        """
        response, error = self.requests_call(
            "get", self.base_url + f"{self.token}/campaigns.json"
        )
        if error:
            return []

        data = response.json()
        items = []

        for item in data.get("items") or []:
            item["binom_id"] = self.extract_binom_id(item["alias"], self.PATTERNS)

            if item.get("activity") == 4 or item["binom_id"] is None:
                continue

            items.append(item)
        items.sort(key=lambda x: x["id"])
        return items

    def get_stats(self, campaign: int) -> list:
        """
        Makes new request to Adsterra's API and gets stats list for the given campaign id.
        Requests only yesterday data for UTC time zone.

        :param campaign:
            int campaign id.
        :return:
            Returns stats list of dicts.
        """
        today = datetime.datetime.utcnow().astimezone(self.TIMEZONE)
        yesterday = today - datetime.timedelta(days=1)
        self.logger.debug(
            yesterday.strftime("%Y-%m-%d") + "-" + today.strftime("%Y-%m-%d")
        )
        response, error = self.requests_call(
            "get",
            self.base_url + f"{self.token}/stats.json",
            params={
                "start_date": yesterday.strftime("%Y-%m-%d"),
                "finish_date": yesterday.strftime("%Y-%m-%d"),
                "group_by": "placement",
                "campaign": campaign,
            },
        )
        if error:
            return []

        data = response.json()
        return data.get("items") or []


class Propellerads(BaseConnect):
    TIMEZONE_NAME = "America/Panama"
    TIMEZONE = pytz.timezone(TIMEZONE_NAME)
    TIMEZONE_OFFSET = (
        int(datetime.datetime.utcnow().astimezone(TIMEZONE).strftime("%z")) // 100
    )
    BASE_URL = cfg.PROPELLERADS_BASE_URL
    PATTERNS = [
            r"\[(\d+)\]",
        ]
    logger = get_cls_logger(__qualname__)

    def get_campaigns(self) -> list:
        """
        Makes request to Propellerads's API and gets campaigns list.
        Generates binom_id for every item from name.

        :return:
            Returns campaigns list of dicts sorted by id.
        """
        response, error = self.requests_call(
            "get",
            self.base_url
            + "adv/campaigns?status[]=3&status[]=4&status[]=5&status[]=6&status[]=7&status[]=8&status[]=9"
            + "&is_archived=0&page_size=500",
            headers={
                "Authorization": "Bearer " + self.token,
            },
        )
        if error:
            return []

        data = response.json()
        items = []

        for item in data.get("result") or []:
            item["binom_id"] = self.extract_binom_id(item["name"], self.PATTERNS)

            if item["binom_id"] is None:
                continue

            items.append(item)
        items.sort(key=lambda x: x["id"])
        return items

    def get_stats(self, campaign: int) -> list:
        """
        Makes new request to Propellerads's API and gets stats list for the given campaign id.
        Requests only yesterday data for local time zone.

        :param campaign:
            int campaign id.
        :return:
            Returns stats list of dicts.
        """
        today = datetime.datetime.utcnow().astimezone(self.TIMEZONE)
        yesterday = today - datetime.timedelta(days=1)
        self.logger.debug(
            yesterday.strftime("%Y-%m-%d") + "-" + today.strftime("%Y-%m-%d")
        )
        response, error = self.requests_call(
            "post",
            self.base_url + "adv/statistics",
            headers={
                "Authorization": "Bearer " + self.token,
            },
            json={
                "group_by": ["zone_id"],
                "day_from": yesterday.strftime("%Y-%m-%d"),
                "day_to": yesterday.strftime("%Y-%m-%d"),
                "tz": datetime.datetime.utcnow()
                .astimezone(self.TIMEZONE)
                .strftime("%z"),
                "campaign_id": [campaign],
            },
        )
        if error:
            return []

        data = response.json()
        return data or []


class Binom(BaseConnect):
    BASE_URL = cfg.BINOM_BASE_URL
    logger = get_cls_logger(__qualname__)

    def get_from_cache_db(self) -> list:
        today = datetime.date.today()

        with sql.connect(cfg.DB_FILE, timeout=10) as con:
            db = con.cursor()
            db.execute(
                "select binom_id,date_s,date_e,timezone,token_val,cost from binom where date=?",
                (today,),
            )
            return db.fetchall()

    def save_update_cost(
        self, camp_id, date_s, date_e, timezone, token_val=None, value=None
    ):
        response, error = self.requests_call(
            "get",
            self.base_url,
            params={
                "page": "save_update_costs",
                "camp_id": camp_id,
                "date": 12,
                "date_s": date_s,
                "date_e": date_e,
                "timezone": timezone,
                "token_number": 1,
                "token_value": token_val,
                "cost": value,
                "api_key": self.token,
            },
        )
        if error:
            return

        self.logger.debug(response.request.url)


def task_adsterra():
    adsterra = Adsterra(token=cfg.ADSTERRA_TOKEN)
    adsterra_campaigns = adsterra.get_campaigns()

    for c in adsterra_campaigns:
        # if c['id'] not in [666530,]:  # filter only campaigns with given ids
        #   continue
        stats = adsterra.get_stats(campaign=c["id"])
        binom_id = c["binom_id"]
        total = 0
        for stat in stats:
            cost = stat["spent"]
            if cost == 0:
                continue
            zone = stat["placement"]
            total += cost

            adsterra.logger.debug(
                "[adsterra] update binom cost %s %s %s %s %s",
                c["id"],
                c["alias"],
                binom_id,
                zone,
                cost,
            )
            today = datetime.datetime.utcnow().astimezone(Adsterra.TIMEZONE)
            yesterday = today - datetime.timedelta(days=1)
            adsterra.save_costs_to_cache_db(
                binom_id,
                yesterday.strftime("%Y-%m-%d"),
                yesterday.strftime("%Y-%m-%d"),
                Adsterra.TIMEZONE_OFFSET,
                zone,
                cost,
            )

        adsterra.logger.debug("[adsterra] binom cost total %s %s", binom_id, total)
        time.sleep(0.050)


def task_propellerads():
    propellerads = Propellerads(token=cfg.PROPELLERADS_TOKEN)
    propellerads_campaigns = propellerads.get_campaigns()

    for c in propellerads_campaigns:
        #     if c['binom_id'] not in ['261',]:  # filter only campaigns with given ids
        #       continue
        stats = propellerads.get_stats(c["id"])
        binom_id = c["binom_id"]
        total = 0
        for stat in stats:
            cost = stat["spent"]
            if cost == 0:
                continue
            zone = stat["zone_id"]
            total += cost

            propellerads.logger.debug(
                "[propellerads] update binom cost %s %s %s %s %s",
                c["id"],
                c["name"],
                binom_id,
                zone,
                cost,
            )
            today = datetime.datetime.utcnow().astimezone(Adsterra.TIMEZONE)
            yesterday = today - datetime.timedelta(days=1)
            propellerads.save_costs_to_cache_db(
                binom_id,
                yesterday.strftime("%Y-%m-%d"),
                yesterday.strftime("%Y-%m-%d"),
                Propellerads.TIMEZONE_OFFSET,
                zone,
                cost,
            )
        propellerads.logger.debug("[propellerads] binom cost total %s", total)
        time.sleep(0.410)


def task_binom():
    binom = Binom(token=cfg.BINOM_TOKEN)
    today_records = binom.get_from_cache_db()

    for rec in today_records:
        binom.save_update_cost(
            camp_id=rec[0],
            date_s=rec[1],
            date_e=rec[2],
            timezone=rec[3],
            token_val=rec[4],
            value=rec[5],
        )


def main():
    if len(sys.argv) > 1:
        try:
            opts, args = getopt.gnu_getopt(sys.argv[1:], "abpv", ["adsterra", "binom", "propellerads", "version"])
        except getopt.GetoptError as err:
            print(err)  # will print something like "option -x not recognized"
            sys.exit(2)

        for opt, arg in opts:
            if opt in ("-a", "--adsterra"):
                task_adsterra()
                sys.exit()
            elif opt in ("-p", "--propellerads"):
                task_propellerads()
                sys.exit()
            elif opt in ("-b", "--binom"):
                task_binom()
                sys.exit()
                use_in_pipe = True
            elif opt in ("-v", "--version"):
                print('Costbin version: %s' % __version__)
                sys.exit()
            else:
                assert False, "unhandled option"

if __name__ == "__main__":
    main()
