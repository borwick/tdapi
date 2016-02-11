# Project introduction

This is a Python API for TeamDynamix. It is not complete--there are
other things you can do in the TeamDynamix API that you can't do with
this code.

# How to use

## Creating a connection

To create your connection, instantiate a TDConnection with your BEID
and WebServicesKey:

	import tdapi

    TD_CONNECTION = tdapi.TDConnection(BEID=BEID,
        WebServicesKey=WebServicesKey)


## Low-level stuff

Reviewing TeamDynamix's API documentation, you may see a call you want
to make that is not already in the API. Great! Especially if you are
fetching data, you probably want the `json_request_roller` method.
This method calls an arbitrary API call and always returns a list of
Python objects:

    models = TD_CONNECTION.json_request_roller(
	             method='get',
				 url_stem='assets/models')
	for model in models:
	  ...

`json_request_roller` calls `json_request` but ensures a list is
always returned. `json_request` calls `request` and then converts the
returned data into Python objects. `request` calls `raw_request`. See
the `raw_request` documentation to see the possible arguments.

## Higher-level stuff ##

*Some* TeamDynamix API stuff has a richer Python wrapper. The style is
along the lines of Django's calls. The trick is that to make the API cleaner the connection needs to be set as a global variable. This is currently done this way:

	import tdapi
	conn_obj = tdapi.TDConnection(BEID='your-BEID', WebServicesKey='your-key)
	tdapi.set_connection(conn_obj)

After you've set the connection, you can say...

    projects = TDProject.objects.current()
	for project in projects:
	    print project.td_url(), project.td_struct['Name']

for example.

# Writing your own higher-level API stuff #

You can use `TDAsset` as a model for creating a new Python class.
You need at least the below code:

    class TDWhateverManager(api.obj.TDObjectManager): pass
	class TDWhatever(api.obj.TDObject): pass
	api.obj.relate_cls_to_manager(TDWhatever, TDWhateverManager)

this `relate_cls_to_manager` function creates `TDWhatever.objects` and
it also tells `TDWhateverManager` about `TDWhatever` so that it can
instantiate objects correctly.

The `api.obj` code is a thin wrapper over the "raw" JSON code.

## Making your stuff somewhat useful ##

If you wanted to then make these classes useful, you would do the following:

### On the manager ###

Create a way to create objects, for example:

    class TDWhateverManager(api.obj.TDObjectManager):
	  def search(self, search_params):
	    return [self.object_class(td_struct)
		        for td_struct
			    in settings.TD_CONNECTION.json_request_roller(
				    method='post',
					url_stem='whatever/search',
					data=search_params)]

(The aforementioned `relate_cls_to_manager` populates `self.object_class`.)

### On the class ###

Create methods as needed, for example:

    class TDWhatever(api.obj.TDObject):
	   def name(self):
	     return self.td_struct['Name']

# Heads up/issues

This code now uses `requests_cache` with a default cache expiration of
1500s. So, if you've been updating TD, the updates may not take effect
for up to 15 minutes.

This code is adapted from some internal code so there may be some
cruft (e.g. weird Python requirements) that are not actually needed
for what you see here.
