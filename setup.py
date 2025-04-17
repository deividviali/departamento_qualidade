from setuptools import setup, find_packages

setup(
    name='correcao_atividades',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'selenium',
        'pandas',
        'openpyxl'
    ],
    entry_points={
        'console_scripts': [
            'loadref=scripts.load_reference:main',
            'runact=scripts.run_activity:main'
        ]
    }
)