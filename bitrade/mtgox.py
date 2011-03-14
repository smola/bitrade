#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright © 2011 Santiago M. Mola <coldwind@coldwind.org>
# Licensed under the terms of the GNU General Public License version 3
#
#
#

from restkit import Manager, Resource

from urllib import urlencode

try:
    import simplejson as json
except ImportError:
    import json # py2.6 only

class AuthError(Exception):
    def __init__(self):
        self.value = 'Authentication error'
    def __str__(self):
        return repr(self.value)

class MtGox(Resource):

    def __init__(self, user=None, password=None, **kwargs):
        self.user = user
        self.password = password
        super(MtGox, self).__init__('https://mtgox.com/code', **kwargs)

    def has_login_data(self):
        return self.user is not None and self.password is not None

    def ticker(self):
        return self.get('/data/ticker.php')

    def market_depth(self):
        return self.get('/data/getDepth.php')

    def recent_trades(self):
        return self.get('/data/getTrades.php')

    def balance(self):
        return self._authenticated_post('/getFunds.php')

    def orders(self):
        return self._authenticated_post('/getOrders.php')

    def buy(self, amount, price):
        return self._authenticated_post('/buyBTC.php', amount, price)

    def sell(self, amount, price):
        return self._authenticated_post('/sellBTC.php', amount, price)

    def cancel(self, oid, typ):
        return self._authenticated_post('/cancelOrder.php',
                params_dict={'oid':oid, 'type':typ})

    def send(self, address, amount):
        return self._authenticated_post('/withdraw.php', group1='BTC',
                address=address, amount=amount)

    def _authenticated_post(self, path, **kwargs):
        if not self.has_login_data():
            raise AuthError()
        params = {'name':self.user, 'pass':self.password}
        params.update(kwargs)
        return self.post(path=path, payload=urlencode(params), headers={'Content-Type':'application/x-www-form-urlencoded'})

    def request(self, *args, **kwargs):
        resp = super(MtGox, self).request(*args, **kwargs)
        return json.loads(resp.body_string())

if __name__ == "__main__":
    mtgox = MtGox()
    print mtgox.ticker()
