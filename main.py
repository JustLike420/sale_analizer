import os
import time
import json
import enum
import requests
from dotenv import load_dotenv

load_dotenv()


class SaleType(str, enum.Enum):
    new = 'Появился новый товар'
    change = 'Изменение цены на товар'

    def __str__(self) -> str:
        return str(self.value)


class Notification:
    def __init__(self, sale_type: SaleType):
        self.sale_type = sale_type
        self.bot_token = os.environ.get("BOT_TOKEN")
        self.chat_id = os.environ.get("CHAT_ID")

    def send(self):
        response = requests.get(
            f'https://api.telegram.org/bot{self.bot_token}/sendMessage'
            f'?chat_id={self.chat_id}&text={self.sale_type}'
        )


class SellWin:
    def __init__(self):
        self.domain = 'https://nest.sellwin.by/'
        self.email = os.environ.get("EMAIL")
        self.password = os.environ.get("PASSWORD")
        self._token = self.get_token()

    def get_token(self) -> str:
        data = json.dumps({"siteId": 1, "email": self.email, "password": self.password})
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(self.domain + 'auth/login', headers=headers, data=data).json()
        token = response.get('token')
        return token

    def get_all_data(self) -> dict:
        all_data = {}
        for page in range(1, 10):
            url = f'https://nest.sellwin.by/element/list/catalog?json=%7B%22clientId%22:60318,%22limit%22:32,%22filter%22:%7B%22props%22:%7B%22isSellout%22:true%7D%7D,%22sort%22:%7B%22orderModel%22:%22%22,%22orderField%22:%22id%22,%22orderBy%22:%22DESC%22%7D%7D&page={page}'
            response = requests.get(url, headers={"Authorization": "Bearer " + self._token})
            if response.status_code == 500:
                print('Invalid token')
                self._token = self.get_token()
                return self.get_all_data()
            else:
                data = response.json()
                if len(data['rows']) != 0:
                    for element in data['rows']:
                        all_data[element['id']] = {
                            'name': element['name'],
                            'price': element['price']['final_price']
                        }
                else:
                    return all_data
        return all_data

    @staticmethod
    def check_data(data: dict):
        new_data = {}

        with open('data.json', 'r', encoding='utf-8') as file:
            json_data = json.load(file)
            """
            {1: {name, price}, 2: {name, price}
            """

        for _id, info in data.items():
            notification_type = None
            _id = str(_id)
            if _id in json_data:
                if json_data[_id]['price'] != info['price']:
                    notification_type = SaleType.change
            else:
                notification_type = SaleType.new

            if notification_type is not None:
                Notification(notification_type).send()

            new_data[_id] = info

        with open('data.json', 'w', encoding='utf-8') as file:
            json.dump(data, file)


if __name__ == '__main__':
    print('~~~START~~~')
    sellWin = SellWin()
    while True:
        data = sellWin.get_all_data()
        sellWin.check_data(data)
        time.sleep(60)
