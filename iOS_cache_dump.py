#/usr/bin/python
import sqlite3
import urlparse
import json
import argparse
import sys
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
	
class CFURL_Cache_BLOB():
	def __init__(self, id, response_obj, request_obj, proto_props, user_info):
		self.id = id
		self.response = readPlistFromString(response_obj)
		self.request = readPlistFromString(request_obj)
		self.proto_props = proto_props
		self.user_info = user_info

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
		#return map(lambda x: format('%s://%s%s', x.req.scheme, self.req.x.req.query, self.cacheMap.values())

	def geBlobs(self):
		pass

        def _process(self):
                self._print("Opening DB File: %s" % (self.dbFile))
                conn = sqlite3.connect(self.dbFile)
		self._getRequests(conn)
		self._getBlobs(conn)
                conn.close()

	def _getRequests(self, conn):
		#entry_ID, version, hash_value, storage_policy, request_key, tme_stamp
                res = conn.execute('SELECT * FROM cfurl_cache_response').fetchall()
		for row in res:
			#self.responses.append(CFURL_Cache_Response(row[0], row[1], row[2], row[3], row[4], row[5]))
			self.cacheMap[row[0]] =  CFURL_Cache_Response(row[0], row[1], row[2], row[3], row[4], row[5])

	def _getBlobs(self, conn):
                #entry_ID, response_object, request_object, proto_props, user_info
                res = conn.execute('SELECT * FROM cfurl_cache_blob_data').fetchall()
		for row in res:
			#self.blobs.append(CFURL_Cache_Blob(row[0], row[1], row[2], row[3], row[4])
			self.blobMap[row[0]] = CFURL_Cache_BLOB(row[0], row[1], row[2], row[3], row[4])
        
        def _print(self, s):
                print("[-] %s" % (s))
        

if __name__ == "__main__":
        '''
        Stuff to support
        -Dump the plists to files
        '''
        parser = argparse.ArgumentParser(description='Python script to inspect iOS Cache.db files',
                epilog='default action is to dump request urls with their respective parameters')
        parser.add_argument('dbfile',
                metavar='db',
                help='Cache.db file to inspect', 
                type=str)
        parser.add_argument('-dump', '--dump-blobs', 
                help='dump request and response blobs associated with each cached response url',
                action='store_true')
	parser.add_argument('-o', '--output',
		metavar='output',
		help='write the request and response blobs as plists in the format <entryid>.req and <entryid>.resp in the folder specified. default is output')

        temp = parser.parse_args()
        args = vars(temp)
        cacheDump = CacheDumper(args['dbfile'])

	for k,v, in cacheDump.cacheMap.items():
		print('CaceDB Entry ID %d'  % (k))
		print('\tURL - %s://%s%s' % (v.req.scheme, v.req.netloc, v.req.path))

		if len(v.params) != 0:
			for qv,qk in v.params.items():
				print('\tParam: %s\tValue: %s' % (str(qv), qk))
		else:
			print('\tNo Params')
		if args['dump_blobs']:
			blob = cacheDump.blobMap[k]
			print('\tRequest: %s' % json.dumps(blob.request, indent=10))
			print('\tResponse: %s' % json.dumps(blob.response, indent=10))
	#getURLs()
	if args['output']:
		dir = args['output']
		if not path.exists(dir):
			makedirs(dir)
		for bk, bv in cacheDump.blobMap.items():
			reqFile = open('%s%s%s.req' % (dir, sep, bk), 'w+')
			reqFile.write(json.dumps(bv.request, indent=4))
			reqFile.close()
			respFile = open('%s%s%s.resp' % (dir, sep, bk), 'w+')
			respFile.write(json.dumps(bv.response, indent=4))
			respFile.close()

