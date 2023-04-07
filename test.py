import httpx, json
import libs.sec as sec

keyapi = "UwU3Api1Passw0rd$=|/523dcC2s342D23hj42Xa"

datatopost = json.dumps({
    "key":"uefRmzmIPnIrPNF34hl711cMoDX4JVyo",
    "uuid": "TESTESTETESTESTESTESTESTTESTESTESTESTESTTESTESTESTESTESTSTESTEST"
})

res = httpx.post("http://127.0.0.1:5000/api/v1/auth",json={ "data" : sec.AESCipher(keyapi).encrypt(datatopost).decode()})
print(json.loads(sec.AESCipher(keyapi).decrypt(res.text))['data'])