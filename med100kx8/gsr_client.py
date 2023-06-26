import requests

response = requests.get('http://192.168.1.125:5000/gsr', stream=True)

for line in response.iter_lines():
    if line:
        print(f'GSR: {line}')
