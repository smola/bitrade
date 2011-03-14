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

def compute_exchange(amount, price_buy, fee=0.0):
    _fee = amount*fee
    return (amount-amount*fee)*(price_buy)

def compute_exchange_round(initial_amount, price_buy, price_sell, fee=0.0):
    return compute_exchange(
            compute_exchange(initial_amount, 1./price_buy, fee),
            price_sell, fee)

def compute_exchange_rounds(initial_amount, price_buy, price_sell, rounds=1, fee=0.0):
    if rounds < 1:
        raise ValueError()

    this_round = compute_exchange_round(initial_amount, price_buy, price_sell, fee)

    if rounds == 1:
        return this_round

    return compute_exchange_rounds(
        this_round, price_buy, price_sell, rounds - 1, fee)
