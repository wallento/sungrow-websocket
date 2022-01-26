import asyncio
import websockets
import json
import requests
import argparse
from terminaltables import AsciiTable

from collections import namedtuple

InverterItem = namedtuple('InverterItem', ['name', 'desc', 'value', 'unit'])

class SungrowWebsocket():
    def __init__(self, host, *, port=8082, locale="en_US"):
        self.host = host
        self.port = port
        self.locale = locale
        self.strings = {}

        self._update_strings()

    def _update_strings(self):
        uri = f"http://{self.host}/i18n/{self.locale}.properties"
        r = requests.get(uri)
        if r.status_code != 200:
            raise Exception(f"Cannot read locale strings from {uri}")
        for line in r.text.splitlines():
            v = line.split("=", 1)
            if len(v) == 2:
                self.strings[v[0]] = v[1]

    async def get_data_async(self):
        data = {}
        async with websockets.connect(f"ws://{self.host}:{self.port}/ws/home/overview") as websocket:
            await websocket.send('{"lang":"en_us","token":"","service":"connect"}')
            d = json.loads(await websocket.recv())
            if d["result_code"] != 1 or d["result_msg"] != "success":
                return data
            token = d["result_data"]["token"]
            # TODO: devicelist
            await websocket.send(json.dumps({"lang":"en_us","token":token,"service":"real","dev_id":"1"}))
            d = json.loads(await websocket.recv())
            if d["result_code"] != 1 or d["result_msg"] != "success":
                return data
            
            for item in d["result_data"]["list"]:
                name = item["data_name"]
                if name.startswith("I18N_COMMON_"):
                    id = name.removeprefix("I18N_COMMON_").lower()
                else:
                    id = name.removeprefix("I18N_").lower()
                data[id] = InverterItem(
                    name = name,
                    desc = self.strings.get(name, name),
                    value = self.strings.get(item["data_value"], item["data_value"]),
                    unit = item["data_unit"]
                )
        return data

    def get_data(self):
        return asyncio.run(self.get_data_async())
        

def main():
    parser = argparse.ArgumentParser(description='Retrieve data from Sungrow inverter using websocket')
    parser.add_argument('host', help='Host (IP or address) of the inverter')
    args = parser.parse_args()

    data = SungrowWebsocket(args.host).get_data()
    table = [["Item", "Value"]] + [[item.desc, f"{item.value} {item.unit}"] for item in data.values()]
    print(AsciiTable(table).table)