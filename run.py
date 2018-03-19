from marketradar import app
from marketradar.config import conf


if __name__ == '__main__':
    app.run(host=conf.get('web','host'), port=conf.get('web','port'), debug=False)