#!/usr/bin/python
import sqlite3
import urlparse
import json
import argparse
import sys
import tempfile
import subprocess
from os import path
from os import sep
from os import makedirs
from lib.biplist import readPlistFromString

class CFURL_Cache_Response():
	def __init__(self, id, version, hash, storage_policy, req_key, ts):
		self.id = id
		self.version = version
		self.storage_policy = storage_policy
		self.req =  urlparse.urlparse(req_key)
		self.ts = ts
		self.params = urlparse.parse_qs(self.req.query, True)
		
	def __str__(self):
		return """============================================================
CacheDB Entry ID {self.id}
	URL - {self.req.scheme}://{self.req.netloc}{self.req.path}
	Params:	{self.req.query}
		""".format(self=self)
				
class CFURL_Cache_BLOB():
	def __init__(self, id, response_obj, request_obj, proto_props, user_info):
		self.id = id
		self.response = readPlistFromString(response_obj)
		self.request = readPlistFromString(request_obj)
		self.proto_props = proto_props
		self.user_info = user_info
		
	def __str__(self):
		return """\tRequest: %s
\tResponse: %s
		""" % (json.dumps(blob.request, indent=10, encoding="ISO-8859-1"), json.dumps(blob.response, indent=10, encoding="ISO-8859-1"))

class CFURL_Response_Data():
	''' cfurl_cache_receiver_data(entry_ID INTEGER PRIMARY KEY, receiver_data BLOB); '''
	def __init__(self, id, receiver_data):
		self.id = id
		self.receiver_data = receiver_data#binascii.unhexlify(receiver_data)
		try:
			temp = tempfile.NamedTemporaryFile()
			temp.write(str(receiver_data))
			p = subprocess.Popen(['file', '-b', temp.name], stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE)
			self.out, self.err = p.communicate()
			#print out
		finally:
			temp.close();
	
	def __str__(self):
		if "empty" in self.out:
			return ""
		elif "ASCII text" in self.out:
			return "\tData:\n%s" % (self.receiver_data)
		else:
			return "\tData: %s" % (self.out)
		
class CacheEntry():
	response = None
	blob = None
	def __init__(self):
		pass

class CacheDumper():
	#Some global variables
	dbFile = ''
	cacheMap = {}
	blobMap = {}
	dataMap = {}

	def __init__(self, dbFile=None):
		self.dbFile = dbFile
		if not path.exists(self.dbFile):
			self._print("Error - file does not exist: %s" % (self.dbFile))
			parser.print_help()
			sys.exit(1)     
		self._process()
		#Set props here

	'''returns a list of the response urls'''
	def getURLs(self):
		return map(lambda x: x.req.geturl(), self.cacheMap.values())

	def geBlobs(self):
		return self.blobMap

	def _process(self):
		self._print("Opening DB File: %s" % (self.dbFile))
		conn = sqlite3.connect(self.dbFile)
		self._getRequests(conn)
		self._getBlobs(conn)
		self._getReceiverData(conn)
		conn.close()

	def _getRequests(self, conn):
		#entry_ID, version, hash_value, storage_policy, request_key, time_stamp
		res = conn.execute('SELECT * FROM cfurl_cache_response').fetchall()
		for row in res:
			self.cacheMap[row[0]] = CFURL_Cache_Response(row[0], row[1], row[2], row[3], row[4], row[5])

	def _getBlobs(self, conn):
		''' 
		cfurl_cache_blob_data(entry_ID INTEGER PRIMARY KEY, response_object BLOB, request_object BLOB, 
							 proto_props BLOB, user_info BLOB);
		'''
		res = conn.execute('SELECT * FROM cfurl_cache_blob_data').fetchall()
		for row in res:
			self.blobMap[row[0]] = CFURL_Cache_BLOB(row[0], row[1], row[2], row[3], row[4])

	def _getReceiverData(self, conn):
		res = conn.execute('SELECT * FROM cfurl_cache_receiver_data').fetchall()
		for row in res:
			self.dataMap[row[0]] = CFURL_Response_Data(row[0], row[1])
		
	def _print(self, s):
		print("[-] %s" % (s))


if __name__ == "__main__":
		'''
		Stuff to support
		-Dump the plists to files
		'''
		parser = argparse.ArgumentParser(description='Python script/lib to inspect iOS Cache.db files',
			epilog='default action is to dump request urls with their respective parameters')
		parser.add_argument('dbfile',
			metavar='db',
			help='Cache.db file to inspect', 
			type=str)
		parser.add_argument('-dump', '--dump-blobs', 
			help='dump request data associated with each cached response url',
			action='store_true')
		parser.add_argument('-o', '--output',
			metavar='output',
			help='write the request and response blobs as plists in the format <entryid>.req and <entryid>.resp in the folder specified. Additionally write all data to {folder}/data. Default folder is output')

		temp = parser.parse_args()
		args = vars(temp)
		cacheDump = CacheDumper(args['dbfile'])

		for id,v in cacheDump.cacheMap.items():
			print(v)
			if args['dump_blobs']:
				blob = cacheDump.blobMap[id]
				print(blob)
				data = cacheDump.dataMap[id]
				print(data)
				
		#getURLs()
		if args['output']:
			dir = args['output']
			if not path.exists(dir):
				makedirs(dir)
			for bk, bv in cacheDump.blobMap.items():
				reqFile = open('%s%s%s.req' % (dir, sep, bk), 'w+')
				reqFile.write(json.dumps(bv.request, indent=4, encoding="ISO-8859-1"))
				reqFile.close()
				respFile = open('%s%s%s.resp' % (dir, sep, bk), 'w+')
				respFile.write(json.dumps(bv.response, indent=4, encoding="ISO-8859-1"))
				respFile.close()
			for dk, dv in cacheDump.dataMap.items():
				if len(dv.receiver_data) > 0:
					dataFile = open('%s%s%s.data' % (dir, sep, dk), 'w+')
					dataFile.write(dv.receiver_data)
					dataFile.close()

