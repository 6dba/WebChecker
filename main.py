import argparse
import os
import requests

from cryptocode import encrypt, decrypt

def parser_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('-l','--login', 
                        type=str, 
                        help='Логин или электронная почта - обязательный параметр')
    parser.add_argument('-p','--password',
                        type=str,
                        help='Пароль от личного кабинета, хранится в зашифрованном виде')
    return parser


if __name__ == "__main__":
    
    parser = parser_args()
    args = parser.parse_args()
   
    os.environ['KEY'] = '666'

    if args.login and args.password:
        
        os.environ['LOGIN'] = encrypt(args.login, os.getenv('KEY'))
        os.environ['PASSWORD'] = encrypt(args.password, os.getenv('KEY'))


        print(os.getenv('LOGIN'), decrypt(os.getenv('LOGIN'), os.getenv('KEY')))
        
    else:
        print('Небходим запуск с параметрами -l (--login) [электронная почта/логин] -p (--password) [пароль] \
              \nНапример: python main.py -l mail@corp.nstu.ru -p password ')

