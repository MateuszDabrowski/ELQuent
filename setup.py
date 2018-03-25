from cx_Freeze import setup, Executable

buildOptions = dict(include_files=['README.md', 'LICENSE', 'utils'],
                    packages=['pyperclip', 're', 'os', 'sys',
                              'platform', 'encodings', 'colorama'],
                    excludes=['user.db', '.gitignore', 'requirements.txt', 'outcomes'])

base = 'Console'

executables = [
    Executable('elquent.py', base=base)
]

setup(name='ELQuent',
      version='1.0',
      description='Eloqua automation utility bundle',
      author='Mateusz Dąbrowski',
      url='https://github.com/MateuszDabrowski/',
      options=dict(build_exe=buildOptions),
      executables=executables)
