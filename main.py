import sanic


app = sanic.Sanic('show_api')

@app.get('/')
async def test(request: sanic.Request) -> sanic.HTTPResponse:
    return sanic.json({'data': 'Hello, world!'})
