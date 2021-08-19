from ..pluginbase import TextProcessor


@TextProcessor.plugin_register('plugin1')
class CleanMarkdownBolds(object):
    def process(self, text):
        return text.replace('**', '')
