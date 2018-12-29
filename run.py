from marketradar import app
from marketradar.config import conf


if __name__ == '__main__':
    app.run(host=conf.get('WEB','host'), port=conf.get('WEB','port'), debug=False)