from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
ext_modules = [
    
    Extension("event6",  ["event6.py"]),
    Extension("event7",  ["event7.py"]),    
    Extension("assistant",  ["assistant.py"]),
    Extension("assistant6",  ["assistant6.py"]),
]
setup(
    name = 'ViPi Assistant',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules
)

