import cherrypy
from newcastle import NewcastleIngest
from sheffield import SheffieldIngest

class Healthz(object):
    @cherrypy.expose
    def healthz(self):
        return "OK!"

cherrypy.tree.mount(Healthz())
cherrypy.tree.mount(SheffieldIngest(), '/data/sheffield')
cherrypy.tree.mount(NewcastleIngest(), '/data/newcastle')

cherrypy.engine.start()
cherrypy.engine.block()