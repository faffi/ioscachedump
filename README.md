iOS Cache Dump
============

Simple python script/library to display the contents of the iOS Cache.db file. Script isn't completely flushed out, but can easily be added to. 

	usage: iOS_cache_dump.py [-h] [-dump] [-o output] db

	Python script to inspect iOS Cache.db files

	positional arguments:
	db                    Cache.db file to inspect

	optional arguments:
	  -h, --help            show this help message and exit
	  -dump, --dump-blobs   dump request and response blobs associated with each
				cached response url
	  -o output, --output output
				write the request and response blobs as plists in the
				format <entryid>.req and <entryid>.resp in the folder
				specified. default is output

	default action is to dump request urls with their respective parameters
