#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright © 2011 Santiago M. Mola <coldwind@coldwind.org>
#
# This file is part of bitrade.
#
# bitrade is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# bitrade is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with bitrade.  If not, see <http://www.gnu.org/licenses/>.
# Licensed under the terms of the GNU General Public License version 3
#

from restkit import Manager, Resource

import time
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

class OrderType(object):
    SELL = 1
    BUY = 2
    ALL = 0

class OrderStatus(object):
    ACTIVE = 1
    NO_FUNDS = 2
    ALL = 0

class _JSONResource(Resource):
    """
    Resource which loads JSON answers.

    FIXME: Integers are being parsed as strings.

    """
    def __init__(self, url, **kwargs):
        super(_JSONResource, self).__init__(url, **kwargs)

    def request(self, *args, **kwargs):
        resp = super(_JSONResource, self).request(*args, **kwargs)
        return json.loads(resp.body_string())

class MtGox(object):
    """
    Mt. Gox interface, using its Trade API: http://mtgox.com/support/tradeAPI
    """

    FEE = 0.0065
    """Mt. Gox transaction fee."""

    def __init__(self, user=None, password=None, cache_time=600):
        """

        @param user User name.
        @param password Password.
        @param cache_time Time in seconds that takes for the cache to expire. Default is 600. Set to 0 for disabling cache.
        """

        self.user = user
        self.password = password
        self._cache_time = cache_time
        self._balance = {'usd':0., 'btc':0}
        self._last_balance = 0.
        self._orders = []
        self._last_orders = 0
        self._r = _JSONResource('https://mtgox.com/code')

    def _get_times_cache(self, last_time):
        current_time = time.time()
        return current_time, current_time - last_time > self._cache_time

    def has_login_data(self):
        """

        @return True if this MtGox instance has user and password set. False otherwise.
        """
        return self.user is not None and self.password is not None

    def ticker(self):
        """

        @return A dict of 'buy', 'high', 'last', 'low', 'sell', 'vol'.
        """
        return self._r.get('/data/ticker.php')['ticker']

    def market_depth(self):
        """

        @return Dict of {'asks':[[price, amount], ...], 'bids':[[price, amount], ...]}
        """
        return self._r.get('/data/getDepth.php')

    def recent_trades(self):
        """

        @return List of recent trades. Each trade is a dict of 'amount', 'date', 'price'.
        """
        return self._r.get('/data/getTrades.php')

    def history(self, time_scale=30):
        """
        History (hidden) method, as used by the MegaChart: https//mtgox.com/trade/megaChart

        @param time_scale History period to retrieve in minutes. 30 by default.
        """
        return self._post('/data/getHistory.php', timeScale=time_scale)

    def balance(self):
        """
        Checks BTC and USD balance.

        @return A dict with 'usd' and 'btc' balance.
        """

        current_time, cache_expired = self._get_times_cache(self._last_balance)
        if cache_expired:
            result = self._authenticated_post('/getFunds.php')
            self._balance = {'btc':result['btcs'], 'usd':result['usds']}
            self._last_balance = current_time
        return self._balance

    def orders(self, typ=OrderType.ALL, status=OrderStatus.ALL):
        """
        Checks placed orders.

        NOTE: Mt. Gox API allows filtering orders by type or status.
              However, for the shake of simplicity and efficiency of cache,
              this methods ask for all orders whenever the cache expires.

        @param typ OrderType.SELL, OrderType.BUY or OrderType.ALL.
        @param status OrderStatus.ACTIVE, OrderStatus.NO_FUNDS or OrderStatus.ALL.
        @return A list of orders. Each order is a dict with 'amount', 'dark', 'date', 'oid', 'price', 'status' and 'type'.

        """

        params = {}
        current_time, cache_expired = self._get_times_cache(self._last_orders)

        #XXX: This code would ask Mt. Gox only for the desired ordered types.
        #if typ != OrderType.ALL:
        #    params['type'] = typ
        #if status != OrderStatus.ALL:
        #    params['status'] = status

        if cache_expired:
            result = self._authenticated_post('/getOrders.php', params)
            self._balance = {'btc':result['btcs'], 'usd':result['usds']}
            self._last_balance = current_time
            self._orders = result['orders']
            self._last_orders = current_time

        types = (typ,) if typ != OrderType.ALL else (OrderType.SELL, OrderType.BUY)
        statuses = (status,) if status != OrderStatus.ALL else (OrderStatus.ACTIVE, OrderStatus.NO_FUNDS)

        orders = []

        for order in self._orders:
            if order['status'] in statuses and order['type'] in types:
               orders.append(dict(order))

        return orders

    def buy(self, amount, price):
        #TODO: Check if it returns all orders.
        return self._authenticated_post('/buyBTC.php', amount, price)

    def sell(self, amount, price):
        #TODO: Check if it returns all orders.
        return self._authenticated_post('/sellBTC.php', amount, price)

    def cancel(self, oid, typ):
        #TODO: Check if it returns all orders.
        return self._authenticated_post('/cancelOrder.php',
            params_dict={'oid':oid, 'type':typ})

    def send(self, address, amount):
        #TODO: Check if it returns all orders.
        return self._authenticated_post('/withdraw.php', group1='BTC',
            address=address, amount=amount)

    def cancel_all(self, typ=OrderType.ALL, status=OrderStatus.ALL):
        result = self.orders(typ, status)
        orders = result['orders']
        order_types = (typ,) if typ != OrderType.ALL else (OrderType.SELL, OrderType.BUY)
        cancelled_orders = []
        for order in orders:
            if order['type'] in order_types:
                self.cancel(order['oid'], order['type'])
                cancelled_orders.append(order)
        return cancelled_orders

    def _authenticated_post(self, path, params_dict={}, **kwargs):
        if not self.has_login_data():
            raise AuthError
        params = {'name':self.user, 'pass':self.password}
        params.update(params_dict)
        return self._post(path, params_dict=params)

    def _post(self, path, params_dict={}, **kwargs):
        params = {}
        params.update(params_dict)
        params.update(kwargs)
        return self._r.post(path=path, payload=urlencode(params), headers={'Content-Type':'application/x-www-form-urlencoded'})

if __name__ == "__main__":
    mtgox = MtGox()
    print mtgox.ticker()
