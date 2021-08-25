class CmdProcessor(object):
    PLUGINS = {}

    def process(self, plugins=()):
        if plugins is ():
            for plugin_name in self.PLUGINS.keys():
                self.PLUGINS[plugin_name]().process()
        else:
            for plugin_name in plugins:
                self.PLUGINS[plugin_name]().process()

    @classmethod
    def plugin_register(cls, plugin_name):
        def wrapper(plugin):
            cls.PLUGINS.update({plugin_name: plugin})
            return plugin
        return wrapper
