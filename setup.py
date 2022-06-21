from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

setup(
    name='nucosen',
    version='3.0.0.2',
    description='Broadcasting system for NUCOSen',
    url='https://github.com/nucosen/Broadcast',
    author='NUCOSen Management Committee',
    author_email='info@nucosen.live',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    python_requires='>=3.10, <4',
    install_requires=open(
        "requirements.txt",
        encoding="utf-16"
    ).read().splitlines(),
    entry_points={
        'console_scripts': [
            'nucosen=nucosen.cli:execute',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/nucosen/Broadcast/issues',
        'Funding': 'https://ofuse.me/nucosen',
        'Source': 'https://github.com/nucosen/Broadcast',
    },
)
