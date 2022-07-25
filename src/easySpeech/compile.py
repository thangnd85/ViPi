#cython: language_level=3
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
ext_modules = [

    Extension("speech",  ["speech.py"]),   
    Extension("record",  ["record.py"]),
    Extension("recognize",  ["recognize.py"]),
    Extension("ml",  ["ml.py"]),
]
setup(
    name = 'ViPi Assistant',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules
)
#python compile.py build_ext --inplace
