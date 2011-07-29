from distutils.core import setup

setup(
    name = "TroveClient",
    version = "0.1.8",
    packages = ['troveclient'],
    author = "Nick Vlku",
    author_email = "n@yourtrove.com",
    description = "The Trove client lets you access Trove services.  Register your app at http://yourtrove.com",
    url = "http://dev.yourtrove.com",
    license = "MIT",
    long_description="See http://dev.yourtrove.com",
    include_package_data = True,
	install_requires= [
		'distribute',
		'oauth==1.0.1',
		'python-dateutil',
		'simplejson'
	]
)

