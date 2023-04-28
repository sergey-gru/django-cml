import os
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string


DEFAULT_FILE_NAME = 'cml_delegate.py'


class Command(BaseCommand):
    help = 'Creates a template file with project cml pipelines'

    def handle(self, file_name=DEFAULT_FILE_NAME, **options):
        file_path = os.path.join(os.getcwd(), file_name)
        if os.path.exists(file_path):
            raise CommandError(f'Error: file "{file_path}" already exists')

        f = open(file_path, 'w')
        f.write(render_to_string('cml/cml_delegate.py'))

        module_name = os.path.basename(file_name)
        msg = f'File: "{file_path}" created.\n'\
              f'To connect you delegate add the following variable to your settings.py:\n\n'\
              f'CML_USER_DELEGATE = \'{module_name}\'\n\n'\
              'Don\'t forget to change this value after moving file.'

        self.stdout.write(msg)
