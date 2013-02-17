from google.appengine.api import memcache
from lib.Transaction import Transaction
from lib.utils import make_key
import time

STALE = 20*60*60
class NoneResult(): pass
class Cache(object):
	cache = {}
	cachekeys = []

	def cachedQuery(self, kind, **kwargs):
		update = kwargs.pop('_update', None)
		key = make_key(kind, **kwargs)
		res = self.get(key)
		
		if not res or update:
			res = Transaction(kind).query(**kwargs)
			self.updatecache(key, res, True)
		return None if type(res) == type(NoneResult) else res

	def get_only(self, key):
		res = self.cache[key] if key in self.cache else memcache.get(key)
		return (None, None) if not res else res

	def get(self, key):
		res, t = self.get_only(key)
		if not res or (time.time() - t) > STALE:
			return None
		self.updatecache(key, res)
		return res

	def updatecache(self, key, res, updateres=False):
		if key in self.cache:
			del self.cachekeys[self.cachekeys.index(key)]
		if updateres:
			t = time.time()
			self.cache[key] = (res, t)
			memcache.set(key, (res, t), STALE)
		self.cachekeys.append(key)
		if len(self.cachekeys) > 100:
			h = self.cachekeys[0]
			del self.cachekeys[0]
			self.cache.pop(h, None)
