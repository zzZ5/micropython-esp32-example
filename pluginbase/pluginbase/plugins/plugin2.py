from ..CmdProcessor import CmdProcessor


@CmdProcessor.plugin_register('plugin2')
class Plugin2(object):
    def process(self):
        print('Plugin2 is running!')
