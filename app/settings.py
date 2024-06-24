import os
from dotenv import load_dotenv


load_dotenv()


class Cfg:
    API_URL = os.getenv('API_URL')
    DB_URL = os.getenv('DATABASE_URL')
    INTERVAL_IN_MINUTES = int(os.getenv('INTERVAL_IN_MINUTES', '10'))


cfg = Cfg()
