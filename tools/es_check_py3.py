import json
import sys
import requests

url = None
username = None
password = None
data = ""
cluster_name = ""

def GET(path, exit=True):
    full_path = url + "/" + path
    r = requests.get(full_path, auth=(username, password), timeout=10)
    if r.status_code != 200 and exit:
        print(r.content)
        sys.exit()
    try:
        content = json.loads(r.content)
        return content
    except:
        print("parse content error: %s" % r.content)
        sys.exit()

def POST(path, body=None, exit=True):
    full_path = url + "/" + path
    r = requests.post(full_path, auth=(username, password), timeout=10)
    if r.status_code != 200 and exit:
        print(r.content)
        sys.exit()
    try:
        content = json.loads(r.content)
        return content
    except:
        print("parse content error: %s" % r.content)
        sys.exit()

# bytes to gb
def gb(b):
    return round(b / 1024 / 1024 / 1024, 2)

# digital to percent
def pt(p):
    return round(p * 100, 2)

# round up
def rd(v):
    return round(v, 2)

def lat(total, time, threshold=1000):
    latency = rd(time / total if total != 0 else 0)
    is_high = False
    if latency > threshold:
        is_high = True
    return (latency, is_high)

def inspect_cluster_status():
    global data
    global cluster_name

    health = GET("_cluster/health")
    stats = GET("_cluster/stats")

    cluster_name = health['cluster_name']

    data += "h1. %s\n" % cluster_name
    data += "h2. Cluster层面\n"

    data += "||集群状态||节点数||索引数||总分片数||未分配分片数||总文档数||内存占用||JVM堆内存占用||存储占用||\n"

    mem_used_gb = gb(stats['nodes']['os']['mem']['used_in_bytes'])
    mem_used_percent = stats['nodes']['os']['mem']['used_percent']
    jvm_heap_used_gb = gb(stats['nodes']['jvm']['mem']['heap_used_in_bytes'])
    jvm_heap_used_percent = pt(jvm_heap_used_gb / gb(stats['nodes']['jvm']['mem']['heap_max_in_bytes']))
    used_store_gb = gb(stats['indices']['store']['size_in_bytes'])
    used_store_percent = pt(used_store_gb / gb(stats['nodes']['fs']['total_in_bytes']))

    data += "|%s|%s|%s|%s|%s|%s|%sGB(%s)|%sGB(%s)|%sGB(%s)|\n" % (
        health['status'], health['number_of_nodes'], stats['indices']['count'],
        stats['indices']['shards']['total'], health['unassigned_shards'], stats['indices']['docs']['count'],
        mem_used_gb, str(mem_used_percent) + "%",
        jvm_heap_used_gb, str(jvm_heap_used_percent) + "%",
        used_store_gb, str(used_store_percent) + "%")

    if health['status'] == "green":
        data += "集群整体处于green健康状态。"
    else:
        data += "集群处于%s非健康状态。" % health['status']

    if used_store_percent > 80:
        data += "集群存储使用率超过80%，请注意存储空间使用，及时扩容或者清理数据。"

    data += "\n\n"


def inspect_node_status():
    global data
    b = {}
    cpu_high = False
    heap_high = False
    disk_high = False

    n = GET('_cat/nodes?format=json')
    a = GET('_cat/allocation?format=json')

    data += "h2. Node层面\n"
    data += "系统资源使用情况：\n"
    data += "||Node||cpu使用率||cpu load(5m)||内存使用率||堆内存使用率||磁盘使用率||分片数||\n"

    for i in n:
        b[i['name']] = [i['cpu'], i['load_5m'], i['ram.percent'], i['heap.percent'], "-", "-"]
        if int(i['cpu']) > 90:
            cpu_high = True
        if int(i['heap.percent']) > 90:
            heap_high = True

    for i in a:
        b[i['node']][4] = i['disk.percent']
        b[i['node']][5] = i['shards']
        if int(i['disk.percent']) > 80:
            disk_high = True

    for i in sorted(b):
        data += "|%s|%s|%s|%s|%s|%s|%s|\n" % (i,
        b[i][0], b[i][1], b[i][2], b[i][3], b[i][4], b[i][5])

    is_health = True
    if cpu_high:
        data += "部分节点的CPU使用率较高，请进行关注。"
        is_health = False
    if heap_high:
        data += "部分节点的JVM Heap使用率较高，请进行关注。"
        is_health = False
    if disk_high:
        data += "部分节点的磁盘使用率较高，请进行关注。"
        is_health = False
    if is_health:
        data += "Node层面系统资源各项指标均正常。"
    data += "\n\n"

def inspect_node_indices():
    global data

    ni = GET('_nodes/stats/indices')
    nodes = sorted(ni['nodes'].items(), key=lambda x: x[1]['name'])

    data += "查询以及索引情况：\n"
    data += "||node||query lat(ms)||fetch lat(ms)||scroll lat(ms)||get lat(ms)||index lat(ms)||refresh lat(ms)||\n"

    for _, node in nodes:
        query_latency, query_high = lat(node['indices']['search']['query_total'],
                                        node['indices']['search']['query_time_in_millis'])
        fetch_latency, fetch_high = lat(node['indices']['search']['fetch_total'],
                                        node['indices']['search']['fetch_time_in_millis'])
        scroll_latency, scroll_high = lat(node['indices']['search']['scroll_total'],
                                          node['indices']['search']['scroll_time_in_millis'])
        get_latency, get_high = lat(node['indices']['get']['total'],
                                    node['indices']['get']['time_in_millis'])
        index_latency, index_high = lat(node['indices']['indexing']['index_total'],
                                        node['indices']['indexing']['index_time_in_millis'])
        refresh_latency, refresh_high = lat(node['indices']['refresh']['total'],
                                            node['indices']['refresh']['total_time_in_millis'])

        data += "|%s|%s|%s|%s|%s|%s|%s|\n" % (
            node['name'], query_latency, fetch_latency,
            scroll_latency, get_latency, index_latency, refresh_latency)

    is_health = True
    if query_high:
        data += "部分节点query操作延迟较高，需要关注。"
        is_health = False
    if fetch_high:
        data += "部分节点fetch操作延迟较高，需要关注。"
        is_health = False
    if scroll_high:
        data += "部分节点scroll操作延迟较高，需要关注。"
        is_health = False
    if get_high:
        data += "部分节点get操作延迟较高，需要关注。"
        is_health = False
    if index_high:
        data += "部分节点index操作延迟较高，需要关注。"
        is_health = False
    if refresh_high:
        data += "部分节点refresh操作延迟较高，需要关注。"
        is_health = False
    if is_health:
        data += "Node层面查询以及索引延迟均正常。"

    data += "\n\n"


def inspect_indices_status(n=20):
    global data

    indices = GET('_cat/indices?format=json&bytes=gb')

    data += "h2. Index层面\n"
    data += "按索引大小显示前%s个索引：\n" % n
    data += "||索引||主分片数||副本分片数||文档数||分片平均大小(GB)||索引大小(GB)||\n"

    n_indices = sorted(indices, key=lambda x: float(x['store.size']), reverse=True)[0:n]
    shard_is_large = False

    for i in n_indices:
        shard_size = float(i['store.size']) / (int(i['pri']) + int(i['rep']))
        if shard_size > 30:
            shard_is_large = True
        data += "|%s|%s|%s|%s|%s|%s|\n" % (
            i['index'], i['pri'], i['rep'], i['docs.count'], shard_size, i['store.size'])

    if shard_is_large:
        data += "部分索引分片大小超过30GB，需要注意。"
    else:
        data += "索引层面数据均正常。"

    data += "\n\n"


def inspect_snapshot_repo():
    global data

    repos = GET("_snapshot")

    data += "h2. 容灾层面\n"

    for repo in repos.keys():
        r = POST("_snapshot/%s/_verify" % repo, exit=False)
        if r.get("status") == 500:
            data += "* Snapshot %s repository 验证失败，请注意。\n" % repo
        else:
            data += "* Snapshot %s repository 验证正常。\n" % repo

    data += "\n\n"

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print('usage: python3 es_check_py3.py <url> [username] [password]')
        sys.exit()

    url = sys.argv[1]

    try:
        username = sys.argv[2]
        password = sys.argv[3]
    except IndexError:
        username = None
        password = None

    inspect_cluster_status()
    inspect_node_status()
    inspect_node_indices()
    inspect_indices_status()
    inspect_snapshot_repo()

    with open(cluster_name + "_report.txt", "w") as f:
        f.write(data)
