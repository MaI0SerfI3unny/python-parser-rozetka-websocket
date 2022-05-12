import websockets,\
    json,\
    asyncio,\
    config,\
    requests
from bs4 import BeautifulSoup
import lxml

dataUrl = open(config.URL_JSON_FILE,'r')
reader = json.loads(dataUrl.read())

print(f"Server listen on {config.SOCKET_PORT}")
connected = set()

def productItemRender(soupResult):
    products = soupResult.find("ul", class_="catalog-grid")\
        .find_all("li", class_="catalog-grid__cell")
    return products


async def echo(websocket,path):
    print("A client connected")
    connected.add(websocket)
    try:
        async  for message in websocket:
            print("Received message from client"+message)
            while True:
                r = requests.get(reader['urls'],
                                 headers=config.HEADER_CONFIG)
                soup = BeautifulSoup(r.text, "lxml")
                page_count = int(soup.find("div", class_="pagination ng-star-inserted")
                                 .find_all("li", class_="pagination__item ng-star-inserted")[-1].text.strip())
                for items in range(1,page_count):
                    r = requests.get('{}page={}/'.format(reader['urls'], items),
                                     headers=config.HEADER_CONFIG)
                    print("Parsing: " + '{}page={}/'
                          .format(reader['urls'], items))
                    soup = BeautifulSoup(r.text, "lxml")
                    for txt in productItemRender(soup):
                        imgUrl = []
                        if txt.find("img", class_="ng-lazyloaded") == None:
                            imgUrl.append('None')
                        else:
                            allImg = txt.findAll("img")
                            for images in allImg:
                                try:
                                    imgUrl.append(images['src'])
                                except Exception as e:
                                    imgUrl.append('None')
                        if txt.find("span",
                                    class_="goods-tile__label promo-label promo-label_type_action ng-star-inserted") != None:
                            renderKupon = txt.find("span",
                                                   class_="goods-tile__label promo-label promo-label_type_action ng-star-inserted").text
                        else: renderKupon = ""

                        infoItem = {
                            "title": txt.find("span", class_="goods-tile__title").text.strip(),
                            "url": txt.find("a", class_="goods-tile__picture ng-star-inserted")["href"],
                            "price": txt.find("span", class_="goods-tile__price-value").text.strip(),
                            "img": imgUrl,
                            "cupon": renderKupon
                        }
                        await websocket.send(json.dumps([json.dumps({'page_count': page_count, 'data': infoItem})]))

                await asyncio.sleep(2)
    except websocket.exceptions.ConnectionClosed as e:
        print("Client disconnected")
        print(e)
    finally:
        connected.remove(websocket)

start = websockets.serve(echo, config.SOCKET_URL, config.SOCKET_PORT)

asyncio.get_event_loop().run_until_complete(start)
asyncio.get_event_loop().run_forever()