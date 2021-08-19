from ..pluginbase import TextProcessor


@TextProcessor.plugin_register('plugin2')
class CleanMarkdownItalic(object):
    def process(self, text):
        return text.replace('--', '')
