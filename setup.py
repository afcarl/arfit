from Cython.Build import cythonize
from distutils.core import setup
import numpy as np

setup(name='ARFit',
      version='0.1',
      description='Code for fitting (C)AR(MA) processes.',
      author='Will M. Farr',
      author_email='w.farr@bham.ac.uk',
      packages=['arfit'],
      scripts=['arfit/run_carma_pack_posterior.py'],
      ext_modules = cythonize('arfit/arn_loops.pyx'),
      include_dirs = [np.get_include()])
      
