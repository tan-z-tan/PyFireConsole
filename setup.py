from setuptools import setup, find_packages

setup(
    name='pyfireconsole',
    version='0.0.9',
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
        'inflect>=0.5.1,<0.6.0',
        'pydantic>=2.0.1,<3.0.0',
        'ipython>=7.0.1,<9.0.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.10',
    ],
)
