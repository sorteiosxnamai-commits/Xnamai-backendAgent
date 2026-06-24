from dotenv import load_dotenv
import os

load_dotenv()

print("ENV APP:", os.getenv("MERCOS_APPLICATION_TOKEN"))
print("ENV COMPANY:", os.getenv("MERCOS_COMPANY_TOKEN"))

MERCOS_APPLICATION_TOKEN = os.getenv("MERCOS_APPLICATION_TOKEN")
MERCOS_COMPANY_TOKEN = os.getenv("MERCOS_COMPANY_TOKEN")

MERCOS_BASE_URL = "https://sandbox.mercos.com/api/v1"