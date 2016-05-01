# -*- coding: utf-8 -*-

import hashlib
import os
import time

import requests
from bs4 import BeautifulSoup
from firebase import firebase


class Crawler(object):
    headers = {'user-agent': ('Mozilla/5.0 '
                              '(Windows NT 6.3; Trident/7.0; rv:11.0) '
                              'like Gecko')}

    def __init__(self):
        firebase_mail = os.environ['FIREBASE_MAIL']
        firebase_secret = os.environ['FIREBASE_SECRET']

        auth = firebase.FirebaseAuthentication(
            firebase_secret, firebase_mail, debug=True, admin=True)
        self.client = firebase.FirebaseApplication(
            'https://azami.firebaseio.com', authentication=auth)

    def fetch_lists(self):
        return self.client.get('/lists', None)

    def fetch_queue(self):
        return self.client.get('/updated', None)

    def generate_hash(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        return hashlib.sha256(soup.get_text()).hexdigest()

    def run(self):
        lists = self.fetch_lists() or {}
        queue = self.fetch_queue() or {}
        targets = set(lists.keys()) - set(queue.keys())
        updated = {}
        errors = {}
        for key in targets:
            time.sleep(1)
            try:
                res = requests.get(lists[key]['url'],
                                   headers=self.headers,
                                   timeout=10)
                res.raise_for_status()
            except requests.ConnectionError as e:
                errors[key] = e
                continue
            hash_ = self.generate_hash(res.text)
            if lists[key]['hash'] == hash_:
                continue
            lists[key]['hash'] = hash_
            updated[key] = lists[key]['url']
        if updated:
            self.client.patch('/lists', lists)
            self.client.patch('/updated', updated)
        if errors:
            self.client.patch('/errors', errors)


if __name__ == '__main__':
    Crawler().run()
