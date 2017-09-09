import requests
import threading
import time
import re

DEBUG = True
USER_AGENT = 'check_proxy.py/1.0'
ACCEPT_LANGUAGE = 'en-US'


class ProxyChecker:
    site = ''
    site_protocol = ''
    site_coding = ''
    proxies = []
    sample = ''
    timeout = 30
    check_times = 11

    proxies_out = []

    def __init__(self):
        self.site_coding = 'utf-8'
        # self.set_sample_site('http://myip.ru/index_small.php')
        self.set_sample_site('https://api.opendota.com/api/matches/34297893235')
        self.get_sample()
        DEBUG and print("Got sample, len = "+str(len(self.sample)))

    def set_proxies(self, proxies_list):
        self.proxies = proxies_list

    def set_proxies_from_file(self, file):
        fr = open(file, 'r')
        iterator = re.finditer('((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}:[0-9]*)', fr.read())
        fr.close()
        self.proxies = [x.group(1) for x in iterator]

        DEBUG and print("Got "+str(len(self.proxies))+" proxies from list")

    def set_sample_site(self, site):
        self.site = site
        self.site_protocol = 'https' if 'https' in self.site[:5].lower() else 'http'  # FIXME https doesnt work LOL

    def set_timeout(self, timeout):
        self.timeout = timeout

    def get_sample(self):
        try:
            r = requests.get(self.site,
                             headers={'user-agent': USER_AGENT},
                             # proxies={'http': '104.236.102.115:8118'},
                             timeout=self.timeout)
            self.sample = r.content.decode(self.site_coding)

            # iterator = re.finditer('\n\t<tr><td>((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3})</td></tr>', self.sample)
            # ip = [x.group(1) for x in iterator][0]
            # print("My ip="+ip)

            print('*'*50)
            print('content=')
            print(self.sample)
            print('*'*50)
        except Exception:
            raise RuntimeError("Cannot get site from main IP.")

    def worker(self, proxy, count):
        try:
            r = requests.get(self.site,
                             headers={'user-agent': USER_AGENT},
                             proxies={self.site_protocol: proxy},
                             timeout=self.timeout)
            content = r.content.decode(self.site_coding)

            # iterator = re.finditer('\n\t<tr><td>((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3})</td></tr>', self.sample)
            # ip = [x.group(1) for x in iterator][0]
            # print("id="+str(proxy_id)+", ip="+ip)

            if content != self.sample:
                while proxy in self.proxies_out:
                    self.proxies_out.remove(proxy)
        except Exception as e:
            DEBUG and print(e)
            while proxy in self.proxies_out:
                self.proxies_out.remove(proxy)
        return

    worker_list = []

    def start(self):
        self.proxies_out = list(self.proxies)
        for count in range(self.check_times):
            DEBUG and print("Check #"+str(count+1)+" of "+str(self.check_times))
            t1 = time.time()
            proxies_out_now = self.proxies_out[:]
            for proxy_id in range(len(proxies_out_now)):
                t = threading.Thread(target=self.worker, args=(proxies_out_now[proxy_id], count))
                self.worker_list.append(t)
                t.start()
            DEBUG and print("Done in "+str(time.time()-t1)+" sec with "+str(len(proxies_out_now))+" started threads")

        DEBUG and print("All threads started, wait for "+str(self.timeout)+" sec.")

        for worker in self.worker_list:
            worker.join()

        print('proxies = '+str(self.proxies_out))
        print('len(proxies)='+str(len(self.proxies_out)))
        # print('-'*60)
        # for i in self.proxies_out:
        #     print(i)
        # print('-'*60)
        return self.proxies_out


if __name__ == '__main__':
    pc = ProxyChecker()
    pc.set_proxies_from_file('proxy')
    pc.start()
