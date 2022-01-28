""" Sungrow inverter interface"""

from __future__ import annotations

import asyncio
from typing import TypedDict
import websockets.client
import json
import aiohttp
import argparse
from terminaltables import AsciiTable  # type: ignore
from collections import namedtuple
from .version import version

InverterItem = namedtuple("InverterItem", ["name", "desc", "value", "unit"])


# Typing of the json we get from the inverter
class Result(TypedDict):
    result_code: int
    result_msg: str
    result_data: ResultData


class ResultDataItems(TypedDict):
    dev_id: str
    data_name: str
    data_value: str
    data_unit: str


class ResultData(TypedDict):
    token: str
    list: list[ResultDataItems]


class SungrowWebsocket:
    """ Websocket API to the Sungrow Inverter"""
    def __init__(self, host: str, *, port: int = 8082, locale: str = "en_US"):
        self.host: str = host
        self.port: int = port
        self.locale: str = locale
        self.strings: dict[str, str] = {}

    async def _update_strings(self):
        self.strings = {}
        url: str = f"http://{self.host}/i18n/{self.locale}.properties"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    text: str = await response.text()
                else:
                    url: str = f"http://{self.host}/i18n/en_US.properties"
                    async with session.get(url) as response:
                        if response.status == 200:
                            text: str = await response.text()
                        else:
                            raise Exception("Unable to get locale")

                for line in text.splitlines():
                    v = line.split("=", 1)
                    if len(v) == 2:
                        self.strings[v[0]] = v[1]

    async def get_data_async(self) -> dict[str, InverterItem]:
        if len(self.strings) == 0:
            await self._update_strings()

        data: dict[str, InverterItem] = {}
        async with websockets.client.connect(
            f"ws://{self.host}:{self.port}/ws/home/overview"
        ) as websocket:
            await websocket.send(
                json.dumps(
                    {"lang": self.locale, "token": "", "service": "connect"}
                )
            )
            d: Result = json.loads(await websocket.recv())
            if d["result_code"] != 1 or d["result_msg"] != "success":
                return data
            token: str = d["result_data"]["token"]

            await websocket.send(
                json.dumps(
                    {
                        "lang": self.locale,
                        "token": token,
                        "service": "devicelist",
                        "type": "0",
                        "is_check_token": "0",
                    }
                )
            )
            d = json.loads(await websocket.recv())
            if d["result_code"] != 1 or d["result_msg"] != "success":
                return data
            dev_id: str = str(d["result_data"]["list"][0]["dev_id"])

            await websocket.send(
                json.dumps(
                    {
                        "lang": self.locale,
                        "token": token,
                        "service": "real",
                        "dev_id": dev_id,
                    }
                )
            )
            d = json.loads(await websocket.recv())
            if d["result_code"] != 1 or d["result_msg"] != "success":
                return data

            for item in d["result_data"]["list"]:
                name = item["data_name"]
                if name.startswith("I18N_COMMON_"):
                    id: str = name.removeprefix("I18N_COMMON_").lower()
                else:
                    id = name.removeprefix("I18N_").lower()
                data[id] = InverterItem(
                    name=name,
                    desc=self.strings.get(name, name),
                    value=self.strings.get(item["data_value"], item["data_value"]),
                    unit=item["data_unit"],
                )

            await websocket.send(
                json.dumps(
                    {
                        "lang": self.locale,
                        "token": token,
                        "service": "real_battery",
                        "dev_id": dev_id,
                    }
                )
            )
            d = json.loads(await websocket.recv())
            if d["result_code"] != 1 or d["result_msg"] != "success":
                return data

            for item in d["result_data"]["list"]:
                name = item["data_name"]
                if name.startswith("I18N_COMMON_"):
                    id: str = name.removeprefix("I18N_COMMON_").lower()
                else:
                    id = name.removeprefix("I18N_").lower()
                data[id] = InverterItem(
                    name=name,
                    desc=self.strings.get(name, name),
                    value=item["data_value"],
                    unit=item["data_unit"],
                )

            await websocket.send(
                json.dumps(
                    {
                        "lang": self.locale,
                        "token": token,
                        "service": "direct",
                        "dev_id": dev_id,
                    }
                )
            )
            d = json.loads(await websocket.recv())
            if d["result_code"] != 1 or d["result_msg"] != "success":
                return data

            from pprint import pprint
            for item in d["result_data"]["list"]:
                if item["name"].startswith("I18N_COMMON_"):
                    item_name = self.strings.get(item["name"][:-3]).format(item["name"][-1])
                else:
                    item_name = item["name"]

                name = item_name + " Voltage"

                id = name.lower().replace(" ", "_")

                data[id] = InverterItem(
                    name=item["name"],
                    desc=name,
                    value=item["voltage"],
                    unit=item["voltage_unit"],
                )

                name = item_name + " Current"

                id = name.lower().replace(" ", "_")

                data[id] = InverterItem(
                    name=item["name"],
                    desc=name,
                    value=item["current"],
                    unit=item["current_unit"],
                )
        return data

    def get_data(self) -> dict[str, InverterItem]:
        return asyncio.run(self.get_data_async())


def main():
    """Command line interface to the inververter"""
    parser = argparse.ArgumentParser(
        description="Retrieve data from Sungrow inverter using websocket"
    )
    parser.add_argument("host", help="Host (IP or address) of the inverter")
    parser.add_argument(
        "--details", action="store_true", help="show more details"
    )
    parser.add_argument('--version', action='version', version=version)
    args: dict[str, InverterItem] = parser.parse_args()

    data: list[InverterItem] = SungrowWebsocket(args.host).get_data()
    if args.details:
        table: list[list[str]] = [["Item", "Value", "ID"]] + [
            [item.desc, f"{item.value} {item.unit}", id]
            for id, item in data.items()
        ]
    else:
        table = [["Item", "Value"]] + [
            [item.desc, f"{item.value} {item.unit}"] for item in data.values()
        ]
    print(AsciiTable(table).table)
