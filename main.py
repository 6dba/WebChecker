import argparse
import os, sys
import requests
import json
import getpass

from typing import Any
from fake_useragent import UserAgent
from cryptocode import encrypt, decrypt
from requests.sessions import session


def _parse_args() -> argparse.ArgumentParser:
    """
    Обработка параметров
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-l','--login', 
                        type=str, 
                        help='Логин или электронная почта. Зашифровано')
    parser.add_argument('-p','--password',
                        type=str,
                        help='Пароль от личного кабинета. Зашифровано')
    return parser


def load_config() -> Any:
    """
    Загрузка конфигурационного файла
    """
    if not os.path.exists('config.json'):
        config = {
            "TOKEN_URL" : "https://login.nstu.ru/ssoservice/json/authenticate?realm=/ido&goto=https://dispace.edu.nstu.ru/user/proceed?login=openam&password=auth",
            "AUTH_URL" : "https://login.nstu.ru/ssoservice/json/authenticate",
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


def logging(login: str, password: str) -> None:
    """
    Авторизация на сайте
    """ 
    agent = UserAgent()
    header = {'User-Agent': str(agent.chrome)}

    config = load_config()

    with requests.Session() as session: 
        _XSRF = session.cookies.get('_xsrf', domain='.nstu.ru')
        token = dict(session.post(config['TOKEN_URL']).json())['authId']
         
        response = session.post(config['AUTH_URL'], headers=header, json={
            'authId': token, 
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
                                )

        print(response.content)



if __name__ == "__main__":
    
    parser = _parse_args()
    args = parser.parse_args()
    
    if not init(args=args):
        sys.exit('Для старта необходимо наличие параметра -l (--login) [электронная почта/логин], либо -l -p (--password) [пароль] \
              \nНапример: python main.py -l mail@stud.nstu.ru | python main.py -l mail@corp.nstu.ru -p password \
              \nПоследующий запуск возможен без параметров')

    logging(
        str(decrypt(os.getenv('LOGIN'), os.getenv('KEY'))), 
        str(decrypt(os.getenv('PASSWORD'), os.getenv('KEY')))
    )
