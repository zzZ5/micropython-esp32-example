from ..CmdProcessor import CmdProcessor


@CmdProcessor.plugin_register('plugin1')
class Plugin1(object):
    def process(self):
        print('Plugin2 is running!')
