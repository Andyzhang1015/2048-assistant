# -- coding: utf-8 --
import time
import requests
import base64
import hashlib
from Crypto.Cipher import AES  # pip install pycryptodome
from Crypto.Util.Padding import unpad

timestamp = str(int(time.time() * 1000))

# 获取sign
def get_sign():
    e = f'client=fanyideskweb&mysticTime={timestamp}&product=webfanyi&key=SRz6r3IGA6lj9i5zW0OYqgVZOtLDQe3e'
    sign = hashlib.md5(e.encode('utf-8')).hexdigest()
    #print(f'sign: {sign}')
    return sign
   

# 获取数据
def get_response(e):
    headers = {
        'Referer': 'https://fanyi.youdao.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    }
    data = {
        'i': e,
        'from': 'auto',
        'to': '',
        'useTerm': 'false',
        #'domain': '0',
        'dictResult': 'true',
        'keyid': 'webfanyi',
        'sign': get_sign(),
        'client': 'fanyideskweb',
        'product': 'webfanyi',
        'appVersion': '1.0.0',
        'vendor': 'web',
        'pointParam': 'client,mysticTime,product',
        'mysticTime': timestamp,
        'keyfrom': 'fanyi.web',
        'mid': '1',
        'screen': '1',
        'model': '1',
        'network': 'wifi',
        'abtest': '0',
        'yduuid': 'abcdefg',
    }
    response = requests.post('https://dict.youdao.com/webtranslate', headers=headers, data=data).text
    #print(f'response: {response}')
    return response

# 数据解密
def encrypt_data(response):
    # 先把密匙和偏移量进行md5加密 digest()是返回二进制的值
    key = hashlib.md5("ydsecret://query/key/B*RGygVywfNBwpmBaZg*WT7SIOUP2T0C9WHMZN39j^DAdaZhAnxvGcCY6VYFwnHl".encode()).digest()
    iv = hashlib.md5("ydsecret://query/iv/C@lZe2YzHtZ2CYgaXKSVfsb7Y4QWHjITPPZ0nQp87fBeJ!Iv6v^6fvi2WN@bYpJ4".encode()).digest()
    cipher = AES.new(key, AES.MODE_CBC, iv)  # 创建一个AES对象（密钥，模式，偏移量）
    ciphertext = base64.urlsafe_b64decode(response)  # 解码为原始的字节串
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return plaintext.decode()

if __name__ == '__main__':
    # e = input('请输入：')
    e = 'good'
    response = get_response(e)
    print(f'原始响应: {response}')
    print(encrypt_data(response))


