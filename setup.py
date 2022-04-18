
from Cython.Build import cythonize
from setuptools import setup, Extension, find_packages
from setuptools_rust import Binding, RustExtension
long_description = """
# Akyuu Bot - The Touhoumon Revised Discord Bot

## Features

On the user end:

- A Pokemon rom parser that parses specific data to use for the bot
    - This includes (but is not limited to):
        - Base Stats
        - Specie names
        - Dex entries
        - Level up movesets
        - Abilities
        - Locations in the wild
- A bot that provides a simple interface to this data to allow users to quickly look up the information they need using
  modern Discord features such as slash commands, modals, ephemeral responses, context commands, and selection menus
- A lot of configuration options to make sure the bot can be accurate through updates
    - May support any Pokemon Fire Red hack given the correct offsets (not tested)
- An interface using modals to for developers to access and modify configuration data through Discord
- An interface for developers to update the patch used by the bot at runtime through either Discord attachments or Mega
  links to a zip archive
- Exception traceback when using developer-only commands (that does not leak user information) for when something
  inevitably goes wrong

View homepage for more information
"""
setup(
    name='akyuu_bot',
    version="0.1.0",
    author='4gboframram',
    description='A Discord bot for the Touhoumon Revised Discord server',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/4gboframram/Akyuu-Bot',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    ext_modules=cythonize([
        Extension('akyuu_bot.sprite_utils.lzss3', ['akyuu_bot/sprite_utils/lzss3.pyx']),
        Extension('akyuu_bot.sprite_utils.sprites', ['akyuu_bot/sprite_utils/sprites.pyx']),
    ]),
    rust_extensions=[RustExtension("akyuu_bot.ups_wrapper", binding=Binding.PyO3,
                                   path="akyuu_bot/ups/Cargo.toml")],

    setup_requires=['cython', 'wheel', 'setuptools-rust'],
    install_requires=['cython', 'wheel', 'setuptools-rust'],
    zip_safe=False,
)
