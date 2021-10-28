import argparse
import os, sys
import requests
import urls
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
                        help='Логин или электронная почта. Зашифровано')
    parser.add_argument('-p','--password',
                        type=str,
                        help='Пароль от личного кабинета. Зашифровано')
    return parser


def init(args: argparse.Namespace) -> bool:
    """
    Инициализация переменных окружения, проверка на наличие аргументов
    """    
    os.environ['KEY'] = '666'

    if args.login and args.password:
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
        _XSRF = session.cookies.get('_xsrf', domain='.nstu.ru')
        token = dict(session.post(urls.TOKEN).json())['authId']
         
        response = session.post(urls.AUTH, headers=header, json={
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
        sys.exit('Небходим запуск с параметрами -l (--login) [электронная почта/логин] -p (--password) [пароль] \
              \nНапример: python main.py -l mail@corp.nstu.ru -p password ')

    logging(
        str(decrypt(os.getenv('LOGIN'), os.getenv('KEY'))), 
        str(decrypt(os.getenv('PASSWORD'), os.getenv('KEY')))
    )
