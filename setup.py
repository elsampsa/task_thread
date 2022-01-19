from setuptools import setup, find_packages
# import sys

# The following line is modified by setver.bash
version = '0.0.0'

# # https://setuptools.readthedocs.io/en/latest/setuptools.html#basic-use
setup(
    # name = "task_thread", # shit.. reserved
    name = "task_virtualthread",
    version = version,
    install_requires = [
        "numpy"
    ],
    packages = find_packages(), # # includes python code from every directory that has an "__init__.py" file in it.  If no "__init__.py" is found, the directory is omitted.  Other directories / files to be included, are defined in the MANIFEST.in file
    include_package_data=True, # # conclusion: NEVER forget this : files get included but not installed
    # # "package_data" keyword is a practical joke: use MANIFEST.in instead
    
    # # WARNING: If you are using namespace packages, automatic package finding does not work, so use this:
    #packages=[
    #    'task_thread'
    #],
    
    #scripts=[
    #    "bin/somescript"
    #],

    # # "entry points" get installed into $HOME/.local/bin
    # # https://unix.stackexchange.com/questions/316765/which-distributions-have-home-local-bin-in-path
    #entry_points={
    #    'console_scripts': [
    #        'my-command = task_thread.subpackage1.cli:main' # this would create a command "my-command" that maps to task_thread.subpackage1.cli method "main"
    #    ]
    #},
    
    # # enable this if you need to run a post-install script:
    #cmdclass={
    #  'install': PostInstallCommand,
    #  },
    
    # metadata for upload to PyPI
    author           = "Sampsa Riikonen",
    author_email     = "sampsa.riikonen@iki.fi",
    description      = "A template for python projects",
    license          = "MIT",
    keywords         = "python sphinx packaging",
    url              = "https://elsampsa.github.io/task_thread/", # project homepage
    
    long_description ="""TaskThread: asyncio made easy""",
    long_description_content_type='text/plain',
    # long_description_content_type='text/x-rst', # this works
    # long_description_content_type='text/markdown', # this does not work
    
    # see: https://autopilot-docs.readthedocs.io/en/latest/license_list.html
    classifiers      =[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',
        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        # 'Operating System :: POSIX :: Linux',
        # 'Topic :: Multimedia :: Video', # set a topic
        # Pick your license as you wish
        # 'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'License :: OSI Approved :: MIT License',
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    #project_urls={ # some additional urls
    #    'Tutorial': 'https://elsampsa.github.io/task_thread/'
    #},
)
