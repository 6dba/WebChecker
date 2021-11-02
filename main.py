import argparse
import os, sys
import requests
import json
import getpass

from json.decoder import JSONDecodeError
from random import random
from typing import Any
from cryptocode import encrypt, decrypt
from requests.sessions import RequestsCookieJar, session



def init_parser() -> argparse.ArgumentParser:
    """
    Обработка параметров
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-l','--login', 
                        type=str, 
                        help='Логин или электронная почта')
    parser.add_argument('-p','--password',
                        type=str,
                        help='Пароль от личного кабинета')
    return parser


def load_config() -> Any:
    """
    Загрузка конфигурационного файла
    """
    if not os.path.exists('config.json'):
        config = {
            "AUTH_TOKEN_URL" : "https://login.nstu.ru/ssoservice/json/authenticate?realm=/ido&goto=https://dispace.edu.nstu.ru/user/proceed?login=openam&password=auth",
            "NSTU_TOKEN_URL" : "https://login.nstu.ru/ssoservice/json/authenticate",
            "DISPACE_TOKEN_URL" : "https://dispace.edu.nstu.ru/user/proceed?login=openam&password=auth",
            "CALENDAR_URL" : "https://dispace.edu.nstu.ru/diclass/calendar/proceed?action=get_event_by_role&group_id=false",
            "LOGIN" : None,
            "PASSWORD" : None
        }

        with open('config.json','w') as file:
            json.dump(config, file)    

    with open('config.json', 'r') as file:
        return json.load(file)


def write_config(conf: dict) -> None:
    """
    Запись в конфигурационный файл
    """
    with open('config.json', 'w') as file:
        json.dump(conf, file)


def init(args: argparse.Namespace) -> bool:
    """
    Инициализация переменных окружения, проверка на наличие аргументов
    """    
    os.environ['KEY'] = '666'
    config = load_config()
    
    if args.login:
        os.environ['LOGIN'] = encrypt(args.login, os.getenv('KEY'))
               
        if args.password:
            os.environ['PASSWORD'] = encrypt(args.password, os.getenv('KEY'))
        
        else:
            try:
                os.environ['PASSWORD'] = encrypt(getpass.getpass('Пароль: '), os.getenv('KEY'))
            except:
                sys.exit()

        config['LOGIN'] = os.getenv('LOGIN')
        config['PASSWORD'] = os.getenv('PASSWORD')
        
        write_config(conf=config)

        return True
    
    if config['LOGIN'] and config['PASSWORD']:
        os.environ['LOGIN'] = config['LOGIN']
        os.environ['PASSWORD'] = config['PASSWORD']
        
        return True        

    return False


def authentification(login: str, password: str) -> Any:
    """
    Авторизация на сайте
    """ 
    config = load_config()

    with requests.Session() as session:
        auth_token = session.post(url=config['AUTH_TOKEN_URL']).json()['authId'] # Получаем токен для авторизации
        json = {
            'authId': auth_token, 
            'template': '',
            'stage': 'JDBCExt1',
            'header': 'Авторизация',
            'callbacks':[
                {
                    'type':'NameCallback',
                    'output': [
                        {
                            'name': 'prompt',
                            'value': 'Логин:'
                        }], 
                    'input': [
                        {
                            'name': 'IDToken1',
                            'value': login
                        }
                    ]
                }, 
                {
                    'type': 'PasswordCallback',
                    'output': [
                        {
                            'name': 'prompt',
                            'value': 'Пароль:'
                        }
                    ], 
                    'input': [
                        {
                            'name': 'IDToken2', 
                            'value': password
                         }
                    ]
                }
            ]
        }
        auth = session.post(url=config['NSTU_TOKEN_URL'], json=json)

        if not auth.ok:
            sys.stdout.write('Неудачная аутентификация!\n')
            sys.exit(f'Код: {auth}\nОтвет от сервера: {auth.text}\n')

        session.cookies.set(name='NstuSsoToken', value=auth.json()['tokenId']) # Если данные верны и аутентификация успешна - устанавливаем токен платформы в куки
        response = session.post(url=config['DISPACE_TOKEN_URL']) # В заголовке ответа получаем Set-Cookie (dispace токен)

        if response.ok:
            sys.stdout.write('Успешная авторизация!\n')
            return session
        
        return None


def processing(session: requests.Session) -> Any:
    """
    Обработка мероприятий расписания
    """
    # https://dispace.edu.nstu.ru/diclass/webinar/index/id_webinar
    # Возможно стоит забрать session_id, math_hash с CALENDAR_URL
    config = load_config()
   
    if not session:
        return None

    with session:
        response = session.post(url=config['CALENDAR_URL'], data={
            'action' : 'get_event_by_role',
            'group_id' : 'false'
        }
                                )
        if response.ok:
            try:
                response.json()
            except JSONDecodeError:
                sys.stdout.write('Неудачное получение списка мероприятий\n')
                sys.exit(f'Код: {response}\nОтвет от сервера: {response.text}\n')
                

            sys.stdout.write('Успешно получен список мероприятий!\n')
            return response.json()['events'], session
        
        sys.stdout.write('Неудачный запрос на получение списка мероприятий\n')
        sys.exit(f'Код: {response}\nОтвет от сервера: {response.text}\n')
        
    
def parse_schedule(events: list) -> Any:
    """
    Разбор возвращенного списка, извлечение мероприятия, если оно is_available
    """
    for event in events:
        event = dict(event)
        
        if event['is_available']:
            return event
    
    return None


def connecting(event: dict, session: requests.Session):
    """
    Подключение к вебинару
    """
    if event['is_available'] and session:
        with session.get(url=event['join_link'], allow_redirects=True, stream=True) as response:
            pass



if __name__ == "__main__":
    
    parser = init_parser()
    args = parser.parse_args()
    
    if not init(args=args):
        sys.exit('Для старта необходимо наличие параметра -l (--login) [электронная почта/логин], либо -l -p (--password) [пароль] \
              \nНапример: python main.py -l mail@stud.nstu.ru | python main.py -l mail@stud.nstu.ru -p password \
              \nПоследующий запуск возможен без параметров')

    session = authentification(
        str(decrypt(os.getenv('LOGIN'), os.getenv('KEY'))), 
        str(decrypt(os.getenv('PASSWORD'), os.getenv('KEY')))
    )

    if session:
        events, session = processing(session=session)
        connecting(event=parse_schedule(events=events), session=session)
