# -*- coding: utf-8 -*-

import json
import sys
import urllib2
import urllib
import base64

reload(sys)
sys.setdefaultencoding('utf-8')

URL = "http://10.255.0.222:9200"
USERNAME = "elastic"
PASSWORD = "ustack"
INDEX = "index2"
ITEMS_PER_PAGE = 1000


def GET(path, exit=True):
    full_path = URL + "/" + path
    request = urllib2.Request(full_path)
    base64string = base64.b64encode('%s:%s' % (USERNAME, PASSWORD))
    request.add_header("Authorization", "Basic %s" % base64string)
    try:
        ret = urllib2.urlopen(request, timeout=10)
    except urllib2.URLError as e:
        print e
        sys.exit()

    content = ret.read()
    status_code = ret.getcode()

    if status_code != 200 and exit:
        sys.exit()
    try:
        return json.loads(content)
    except:
        print "parse content error: %s" % content
        sys.exit()


def POST(path, body={}, exit=True):
    full_path = URL + "/" + path
    request = urllib2.Request(full_path, data=json.dumps(body))
    base64string = base64.b64encode('%s:%s' % (USERNAME, PASSWORD))
    request.add_header("Authorization", "Basic %s" % base64string)
    request.add_header("Content-Type", "application/json")
    try:
        ret = urllib2.urlopen(request, timeout=10)
    except urllib2.URLError as e:
        if exit:
            print e
            sys.exit()
        else:
            return {"status": e.code}

    content = ret.read()
    status_code = ret.getcode()

    if status_code != 200 and exit:
        sys.exit()
    try:
        return json.loads(content)
    except:
        print "parse content error: %s" % content
        sys.exit()


body = {
    "size": 0,
    "aggs" : {
        "rec_nos": {
            "composite" : {
                "size": ITEMS_PER_PAGE,
                "sources" : [
                    { "rec_no": { "terms" : { "field": "rec_no" } } }
                ]
            }
        }
    }
}

with open(INDEX+".txt", "w") as f:
    while True:
        result = POST("%s/_search" % INDEX, body=body)
        for bucket in result['aggregations']['rec_nos']['buckets']:
            f.write(str(bucket['key']['rec_no'])+"\n")
        after = result['aggregations']['rec_nos'].get('after_key')
        if after:
            body['aggs']['rec_nos']['composite']['after'] = after
            print "getting after %s" % after.get('rec_no')
        else:
            break
