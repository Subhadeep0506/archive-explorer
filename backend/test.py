import requests

URL = "https://arxiv.org/pdf/2504.19565v3"
# URL = "https://arxiv.org/pdf/2403.09676v1"

data = requests.get(URL)
filename = URL.split("/")[-1] + ".pdf"
with open(filename, "wb") as f:
    f.write(data.content)
print(f"Downloaded {filename} from {URL}")
