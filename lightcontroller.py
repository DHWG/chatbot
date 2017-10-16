#!/usr/bin/python

import socket
import fcntl
import re
import os
import errno
import struct
from threading import Thread
from time import sleep
import sys

class lightcontroller():

    @classmethod
    def instance(cls):
        if '_instance' not in cls.__dict__:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.RUNNING = True
        self.detected_bulbs = {}
        self.bulb_idx2ip = {}
        self.DEBUGGING = False
        self.current_command_id = 0
        self.MCAST_GRP = '239.255.255.250'
        self.scan_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        fcntl.fcntl(self.scan_socket, fcntl.F_SETFL, os.O_NONBLOCK)
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket.bind(("", 1982))
        fcntl.fcntl(self.listen_socket, fcntl.F_SETFL, os.O_NONBLOCK)
        self.mreq = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)
        self.listen_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, self.mreq)
        self.m_detection_thread = Thread(target=self.bulbs_detection_loop)
        self.m_detection_thread.start()
        sleep(1)


    def next_cmd_id(self):
        self.current_command_id += 1
        return self.current_command_id


    def send_search_broadcast(self):
        '''
        multicast search request to all hosts in LAN, do not wait for response
        '''
        multicase_address = (self.MCAST_GRP, 1982)
        msg = "M-SEARCH * HTTP/1.1\r\n"
        msg = msg + "HOST: 239.255.255.250:1982\r\n"
        msg = msg + "MAN: \"ssdp:discover\"\r\n"
        msg = msg + "ST: wifi_bulb"
        self.scan_socket.sendto(msg, multicase_address)


    def bulbs_detection_loop(self):

        search_interval = 2000
        read_interval = 100
        time_elapsed = 0

        while self.RUNNING:
            if time_elapsed % search_interval == 0:
                self.send_search_broadcast()

            # scanner
            while True:
                try:
                    data = self.scan_socket.recv(2048)
                except socket.error, e:
                    err = e.args[0]
                    if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                        break
                    else:
                        print e
                        sys.exit(1)
                self.handle_search_response(data)

            # passive listener
            while True:
                try:
                    data, addr = self.listen_socket.recvfrom(2048)
                except socket.error, e:
                    err = e.args[0]
                    if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                        break
                    else:
                        print e
                        sys.exit(1)
                self.handle_search_response(data)

            time_elapsed += read_interval
            sleep(read_interval / 1000.0)
        self.scan_socket.close()
        self.listen_socket.close()


    def get_param_value(self, data, param):
        '''
        match line of 'param = value'
        '''
        param_re = re.compile(param + ":\s*([ -~]*)")  # match all printable characters
        match = param_re.search(data)
        value = ""
        if match != None:
            value = match.group(1)
            return value


    def handle_search_response(self,data):
        '''
        Parse search response and extract all interested data.
        If new bulb is found, insert it into dictionary of managed bulbs.
        '''
        location_re = re.compile("Location.*yeelight[^0-9]*([0-9]{1,3}(\.[0-9]{1,3}){3}):([0-9]*)")
        match = location_re.search(data)
        if match == None:
            return

        host_ip = match.group(1)
        if self.detected_bulbs.has_key(host_ip):
            bulb_id = self.detected_bulbs[host_ip][0]
        else:
            bulb_id = len(self.detected_bulbs) + 1
        host_port = match.group(3)
        model = self.get_param_value(data, "model")
        power = self.get_param_value(data, "power")
        bright = self.get_param_value(data, "bright")
        rgb = self.get_param_value(data, "rgb")
        # use two dictionaries to store index->ip and ip->bulb map
        self.detected_bulbs[host_ip] = [bulb_id, model, power, bright, rgb, host_port]
        self.bulb_idx2ip[bulb_id] = host_ip
        #print(self.detected_bulbs)


    def display_bulb(self,idx):
        if not self.bulb_idx2ip.has_key(idx):
            print "error: invalid bulb idx"
            return
        bulb_ip = self.bulb_idx2ip[idx]
        model = self.detected_bulbs[bulb_ip][1]
        power = self.detected_bulbs[bulb_ip][2]
        bright = self.detected_bulbs[bulb_ip][3]
        rgb = self.detected_bulbs[bulb_ip][4]
        print str(idx) + ": ip=" \
              + bulb_ip + ",model=" + model \
              + ",power=" + power + ",bright=" \
              + bright + ",rgb=" + rgb


    def display_bulbs(self):
        print str(len(self.detected_bulbs)) + " managed bulbs"
        for i in range(1, len(self.detected_bulbs) + 1):
            self.display_bulb(i)


    def operate_on_bulb(self,idx, method, params):
        '''
        Operate on bulb; no gurantee of success.
        Input data 'params' must be a compiled into one string.
        E.g. params="1"; params="\"smooth\"", params="1,\"smooth\",80"
        '''
        if not self.bulb_idx2ip.has_key(idx):
            print "error: invalid bulb idx"
            return

        bulb_ip = self.bulb_idx2ip[idx]
        port = self.detected_bulbs[bulb_ip][5]
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print "connect ", bulb_ip, port, "..."
            tcp_socket.connect((bulb_ip, int(port)))
            msg = "{\"id\":" + str(self.next_cmd_id()) + ",\"method\":\""
            msg += method + "\",\"params\":[" + params + "]}\r\n"
            tcp_socket.send(msg)
            tcp_socket.close()
        except Exception as e:
            print "Unexpected error:", e


    def toggle_bulb(self):
        self.operate_on_bulb(1, "toggle", "")

    def set_bright(self,idx, bright):
        self.operate_on_bulb(idx, "set_bright", str(bright))

    def bright(self, bright):
        self.set_bright(1, str(bright))


    def print_cli_usage(self):
        print "Usage:"
        print "  q|quit: quit bulb manager"
        print "  h|help: print this message"
        print "  t|toggle <idx>: toggle bulb indicated by idx"
        print "  b|bright <idx> <bright>: set brightness of bulb with label <idx>"
        print "  r|refresh: refresh bulb list"
        print "  l|list: lsit all managed bulbs"


    def get_status(self):
        bulb_ip = self.bulb_idx2ip[1]
        power = self.detected_bulbs[bulb_ip][2]
        #print(power)
        print(self.detected_bulbs[bulb_ip])
        return power



    def notify(self):
        status = self.get_status()
        if status == "off":
            self.toggle_bulb()
        idx = 1
        method = "set_bright"
        params = [25, 100]
        if not self.bulb_idx2ip.has_key(idx):
            print "error: invalid bulb idx"
            return

        bulb_ip = self.bulb_idx2ip[idx]
        port = self.detected_bulbs[bulb_ip][5]
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print "connect ", bulb_ip, port, "..."
            tcp_socket.connect((bulb_ip, int(port)))
            msg1 = "{\"id\":" + str(self.next_cmd_id()) + ",\"method\":\""
            msg1 += method + "\",\"params\":[" + str(params[0]) + "]}\r\n"
            msg2 = "{\"id\":" + str(self.next_cmd_id()) + ",\"method\":\""
            msg2 += method + "\",\"params\":[" + str(params[1]) + "]}\r\n"

            delay = 0.4
            repetitions = 3
            for i in range(repetitions):
                #print("cycle:" + str(i + 1))
                tcp_socket.send(msg1)
                sleep(delay)
                tcp_socket.send(msg2)
                sleep(delay)
            tcp_socket.close()
        except Exception as e:
            print "Unexpected error:", e

        if status != self.get_status():
            self.toggle_bulb()

        return status







