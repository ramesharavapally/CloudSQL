from setuptools import setup, find_packages

setup(
    name='erpsqlapp',
    version='1.0',
    author='Ramesh Arvapalli',
    author_email='ramesh.arva7@email.com',
    description='A Streamlit application for managing cloud connections.',    
    long_description_content_type='text/markdown',    
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'streamlit',
        'requests',
        'pandas'
    ],
     entry_points={
        'console_scripts': [
            'erpsqlapp=cloudsql.ERPCloudConsole:main'
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License Self',
        'Operating System :: OS Independent',
    ],
)
