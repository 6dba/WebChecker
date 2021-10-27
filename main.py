import argparse
import os, sys
import requests
import config
import json

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
                        help='Логин или электронная почта - обязательный параметр')
    parser.add_argument('-p','--password',
                        type=str,
                        help='Пароль от личного кабинета, хранится в зашифрованном виде')
    return parser


def init(args: argparse.Namespace) -> bool:
    """
    Инициализация переменных окружения, проверка на наличие аргументов
    """    
    if args.login and args.password:
        os.environ['KEY'] = '666'
        os.environ['LOGIN'] = encrypt(args.login, os.getenv('KEY'))
        os.environ['PASSWORD'] = encrypt(args.password, os.getenv('KEY'))

        return True
    
    return False


def logging(login: str, password: str) -> None:
    """
    Авторизация на сайте
    """ 
    agent = UserAgent()
    header = {'User-Agent': str(agent.chrome)}

    with requests.Session() as session:
        session.get(url=config.AUTH_URL, headers=header)

        config._XSRF = session.cookies.get('_xsrf', domain='.nstu.ru')
        
        token = dict(session.post(config.TOKEN_URL).json())['authId']
         
        response = session.post(config.AUTH_URL, json={
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
        
        print(response.json())



if __name__ == "__main__":
    
    parser = _parse_args()
    args = parser.parse_args()

    if not init(args=args):
        sys.exit('Небходим запуск с параметрами -l (--login) [электронная почта/логин] -p (--password) [пароль] \
              \nНапример: python main.py -l mail@corp.nstu.ru -p password ')

    logging(
        str(decrypt(os.getenv('LOGIN'), os.getenv('KEY'))), 
        str(decrypt(os.getenv('PASSWORD'), os.getenv('KEY')))
    )
