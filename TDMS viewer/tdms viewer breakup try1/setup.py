"""
TDMS Viewer Setup Script
"""

import os
from setuptools import setup, find_packages

# Read version from package
def get_version():
    version_file = os.path.join('src', '__init__.py')
    with open(version_file, 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip("'").strip('"')
    return '0.0.1'

# Read long description from README
def read_long_description():
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ''

# Project dependencies
REQUIRED_PACKAGES = [
    'PyQt5>=5.15.0',
    'numpy>=1.19.0',
    'nptdms>=1.3.0',
    'pyqtgraph>=0.12.0',
    'scipy>=1.7.0'
]

# Development dependencies
DEVELOPMENT_PACKAGES = [
    'pytest>=6.0.0',
    'pytest-qt>=4.0.0',
    'pytest-cov>=2.0.0',
    'black>=21.0.0',
    'flake8>=3.9.0',
    'mypy>=0.900',
    'sphinx>=4.0.0',
    'sphinx-rtd-theme>=0.5.0'
]

setup(
    name='tdms-viewer',
    version=get_version(),
    author='TDMS Viewer Development Team',
    author_email='maintainers@tdmsviewer.org',
    description='A PyQt-based viewer for TDMS files with advanced visualization capabilities',
    long_description=read_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/tdms-viewer',
    
    # Package configuration
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    include_package_data=True,
    
    # Dependencies
    python_requires='>=3.7',
    install_requires=REQUIRED_PACKAGES,
    extras_require={
        'dev': DEVELOPMENT_PACKAGES,
        'test': [
            'pytest>=6.0.0',
            'pytest-qt>=4.0.0',
            'pytest-cov>=2.0.0'
        ],
        'docs': [
            'sphinx>=4.0.0',
            'sphinx-rtd-theme>=0.5.0'
        ]
    },
    
    # Entry points
    entry_points={
        'console_scripts': [
            'tdms-viewer=tdms_viewer.main:main',
        ],
        'gui_scripts': [
            'tdms-viewer-gui=tdms_viewer.main:main',
        ]
    },
    
    # Package metadata
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Visualization',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Operating System :: OS Independent',
        'Environment :: X11 Applications :: Qt',
    ],
    keywords='tdms, data visualization, scientific data, measurement data',
    
    # Package data
    package_data={
        'tdms_viewer': [
            'resources/*.png',
            'resources/*.ico',
            'resources/*.json',
            'config/*.json',
        ],
    },
    
    # Project URLs
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/tdms-viewer/issues',
        'Source': 'https://github.com/yourusername/tdms-viewer/',
        'Documentation': 'https://tdms-viewer.readthedocs.io/',
    },
    
    # Build configuration
    zip_safe=False,
    platforms=['any'],
    
    # Testing configuration
    test_suite='tests',
    tests_require=[
        'pytest>=6.0.0',
        'pytest-qt>=4.0.0',
        'pytest-cov>=2.0.0'
    ],
)

# Post-installation setup
def post_install():
    """Perform post-installation tasks"""
    import sys
    import site
    import shutil
    from pathlib import Path
    
    # Get site-packages directory
    site_packages = site.getsitepackages()[0]
    
    # Create necessary directories
    dirs_to_create = [
        'config',
        'logs',
        'resources'
    ]
    
    package_dir = os.path.join(site_packages, 'tdms_viewer')
    for directory in dirs_to_create:
        os.makedirs(os.path.join(package_dir, directory), exist_ok=True)
    
    # Copy default configuration
    default_config = os.path.join('src', 'config', 'tdms_viewer_config.json')
    if os.path.exists(default_config):
        shutil.copy2(
            default_config,
            os.path.join(package_dir, 'config', 'tdms_viewer_config.json')
        )
    
    # Copy resources
    resource_files = [
        'TDMS viewer icon.png',
        'TDMS viewer icon.ico'
    ]
    
    for resource in resource_files:
        src = os.path.join('src', 'resources', resource)
        if os.path.exists(src):
            shutil.copy2(
                src,
                os.path.join(package_dir, 'resources', resource)
            )

if __name__ == '__main__':
    # If this script is being run directly, perform post-installation tasks
    post_install()
