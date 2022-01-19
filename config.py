from dotenv import load_dotenv
import os
import random
load_dotenv()
SECRET_KEY = str(os.getenv('SECRET_KEY'))
extension_accept_list = ["jpg", "png", "jpeg"]

