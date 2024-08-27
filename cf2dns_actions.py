# Mail: tongdongdong@outlook.com
import random
import time
import json
import requests
import os
import traceback
from dns.qCloud import QcloudApiv3 # QcloudApiv3 DNSPod 的 API 更新了 github@z0z0r4
from dns.aliyun import AliApi
from dns.huawei import HuaWeiApi
import sys

#可以从https://shop.hostmonit.com获取
KEY = os.environ["KEY"]  #"o1zrmHAF"
#CM:移动 CU:联通 CT:电信 AB:境外 DEF:默认
#修改需要更改的dnspod域名和子域名
DOMAINS = json.loads(os.environ["DOMAINS"])  #{"hostmonit.com": {"@": ["CM","CU","CT"], "shop": ["CM", "CU", "CT"], "stock": ["CM","CU","CT"]},"4096.me": {"@": ["CM","CU","CT"], "vv": ["CM","CU","CT"]}}
#腾讯云后台获取 https://console.cloud.tencent.com/cam/capi
SECRETID = os.environ["SECRETID"]    #'AKIDV**********Hfo8CzfjgN'
SECRETKEY = os.environ["SECRETKEY"]   #'ZrVs*************gqjOp1zVl'
#默认为普通版本 不用修改
AFFECT_NUM = 5
#DNS服务商 如果使用DNSPod改为1 如果使用阿里云解析改成2  如果使用华为云解析改成3
DNS_SERVER = 3
#如果试用华为云解析 需要从API凭证-项目列表中获取
REGION_HW = 'ap-southeast-1'
#如果使用阿里云解析 REGION出现错误再修改 默认不需要修改 https://help.aliyun.com/document_detail/198326.html
REGION_ALI = 'cn-hongkong'
#解析生效时间，默认为600秒 如果不是DNS付费版用户 不要修改!!!
TTL = 1
#v4为筛选出IPv4的IP  v6为筛选出IPv6的IP
if len(sys.argv) >= 2:
    RECORD_TYPE = sys.argv[1]
else:
    RECORD_TYPE = "A"


def get_optimization_ip():
    try:
        headers = headers = {'Content-Type': 'application/json'}
        data = {"key": KEY, "type": "v4" if RECORD_TYPE == "A" else "v6"}
        response = requests.post('https://api.hostmonit.com/get_optimization_ip', json=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print("CHANGE OPTIMIZATION IP ERROR: REQUEST STATUS CODE IS NOT 200")
            return None
    except Exception as e:
        print("CHANGE OPTIMIZATION IP ERROR: " + str(e))
        return None

def changeDNS(line, s_info, c_info, domain, sub_domain, cloud):
    #...
    if create_num > 0:
        for i in range(create_num):
            if len(c_info) == 0:
                break
            # 根据新的 IP 结构获取 IP
            cf_ip = c_info.pop(random.randint(0,len(c_info)-1))
            # 如果 cf_ip 不是期望的 IP 格式，可能需要进一步处理
            if cf_ip in str(s_info):
                continue
            #...
def main(cloud):
    global AFFECT_NUM, RECORD_TYPE
    if len(DOMAINS) > 0:
        try:
            cfips = get_optimization_ip()
            if cfips == None or cfips["code"]!= 200:
                print("GET CLOUDFLARE IP ERROR: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) )
                return
            # 假设新的 IP 列表没有分类，直接使用一个单一的 IP 列表
            temp_cfips = cfips.copy()
            for domain, sub_domains in DOMAINS.items():
                for sub_domain, lines in sub_domains.items():
                    if DNS_SERVER == 1:
                        ret = cloud.get_record(domain, 20, sub_domain, "CNAME")
                        if ret["code"] == 0:
                            for record in ret["data"]["records"]:
                                if record["line"] == "移动" or record["line"] == "联通" or record["line"] == "电信":
                                    retMsg = cloud.del_record(domain, record["id"])
                                    if(retMsg["code"] == 0):
                                        print("DELETE DNS SUCCESS: ----Time: "  + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----DOMAIN: " + domain + "----SUBDOMAIN: " + sub_domain + "----RECORDLINE: "+record["line"] )
                                    else:
                                        print("DELETE DNS ERROR: ----Time: "  + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----DOMAIN: " + domain + "----SUBDOMAIN: " + sub_domain + "----RECORDLINE: "+record["line"] + "----MESSAGE: " + retMsg["message"] )
                    ret = cloud.get_record(domain, 100, sub_domain, RECORD_TYPE)
                    if DNS_SERVER!= 1 or ret["code"] == 0 :
                        if DNS_SERVER == 1 and "Free" in ret["data"]["domain"]["grade"] and AFFECT_NUM > 2:
                            AFFECT_NUM = 2
                        info = []
                        for record in ret["data"]["records"]:
                            temp_info = {}
                            temp_info["recordId"] = record["id"]
                            temp_info["value"] = record["value"]
                            info.append(temp_info)
                        for line in lines:
                            # 不再区分不同类型的 IP，直接使用单一的 IP 列表
                            changeDNS("DEFAULT", info, temp_cfips, domain, sub_domain, cloud)
        except Exception as e:
            print("CHANGE DNS ERROR: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----MESSAGE: " + str(traceback.print_exc()))

if __name__ == '__main__':
    if DNS_SERVER == 1:
        cloud = QcloudApiv3(SECRETID, SECRETKEY)
    elif DNS_SERVER == 2:
        cloud = AliApi(SECRETID, SECRETKEY, REGION_ALI)
    elif DNS_SERVER == 3:
        cloud = HuaWeiApi(SECRETID, SECRETKEY, REGION_HW)
    main(cloud)