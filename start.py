import argparse
from app import app

parser = argparse.ArgumentParser(description='run poker site', prog='start')
parser.add_argument('-p',
                    metavar='port',
                    action='store',
                    type=int,
                    help='run poker site on port port'
                    )
args = parser.parse_args()
app.run(host='127.0.0.1', port=args.p)
