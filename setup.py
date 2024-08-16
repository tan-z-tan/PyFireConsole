from setuptools import setup, find_packages

setup(
    name='pyfireconsole',
    version='0.1.1',
    author='Makoto Tanji',
    author_email='tanji.makoto@gmail.com',
    description='An interactive console for Firestore based on Python ORM',
    long_description=open('README.md', 'r').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/tan-z-tan/pyfireconsole',
    packages=find_packages(),
    python_requires='>=3.8.0',
    install_requires=[
        'google-cloud-firestore>=2.0.0,<3.0.0',
        'google-auth>=2.0.0,<3.0.0',
        'inflection>=0.5.1,<0.6.0',
        'pydantic>=2.0.1,<3.0.0',
        'ipython>=7.0.1,<9.0.0',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries",
    ],
    entry_points={
        'console_scripts': [
            'pyfireconsole = pyfireconsole.console.run_console:main',
        ],
    },
)
