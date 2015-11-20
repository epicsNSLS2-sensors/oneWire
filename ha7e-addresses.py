# * coding: utf-8 *

from __future__ import print_function
import os
import sys
import time

from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver
from twisted.internet import defer

if len(sys.argv) < 3:
    print('Usage: %s moxa_ip moxa_port' % (sys.argv[0], ))
    print('(moxa_port is usually 4001)')
    sys.exit(1)

ip_address, port = sys.argv[1], int(sys.argv[2])

print('Moxa: %s:%d' % (ip_address, port))

def hex_str_to_int(h):
    odds = h[::2]
    evens = h[1::2]
    bytes_ = list('%s%s' % (o, e) for o, e in zip(odds, evens))
    return [int(b, 16) for b in bytes_]


def convert_temp(msb, lsb):
    sign = (msb & 0x08) >> 3
    msb = (msb & 0x03)
    temp_c = msb * (2 ** 4) + lsb * (2 ** -4)
    if sign:
        temp_c = -temp_c
    return temp_c

CONVERSION_TIME = 0.75 # in seconds
temperatures = {}
running = True


@defer.inlineCallbacks
def convert_loop(ha7e, addresses):
    while running:
        # Start temperature conversion on all devices
        t0 = time.time()
        for addr in addresses:
            _ = yield ha7e.send_query(addr, 'W', '44')
            #self.convert_end[addr] = time.time() + CONVERSION_TIME
        t1 = time.time()
        start_elapsed = (t1 - t0)
        #print('* Start conversion elapsed', start_elapsed)
        os.system('clear')

        t0 = time.time()
        time.sleep(max(0, CONVERSION_TIME - start_elapsed))
        temps = []
        for addr in addresses:
            ret = yield ha7e.send_query(addr, 'W', 'BE' + 'FF' * 9,
                                        ret_int=True)

            echo_be, lsb, msb, th, tl, conf, res_ff, res_1, res_10, crc = ret
            temp_c = convert_temp(msb, lsb)
            print('%s %.3f C' % (addr, temp_c))

            path = os.path.join('data', '%s.txt' % addr)
            with open(path, 'at') as f:
                print('%.5f' % temp_c, file=f)

            if addr not in temperatures:
                temperatures[addr] = []

            temperatures[addr].append(temp_c)
            temps.append(temp_c)

        t1 = time.time()

        convert_elapsed = (t1 - t0)
        elapsed = start_elapsed + convert_elapsed
        print('* Min temperature %.4f Max temperature %.4f' % (min(temps), max(temps)))
        print('* Total time %.2f s per sensor %.2f s' % (elapsed, elapsed / len(addresses)))
        print()
        break


class HA7EClient(LineReceiver):
    delimiter = '\r'
    def __init__(self):
        self._searched = False
        self._addresses = set([])
        self._query_idx = 0
        self._deferred = None
        self.convert_end = {}

    def connectionMade(self):
        print('Connected')
        if not self._searched:
            self.sendLine('S')
        else:
            self.start_loop()

    @defer.inlineCallbacks
    def start_loop(self):
        _ = yield convert_loop(self, self._addresses)
        reactor.stop()

    @property
    def addr(self):
        return self._addresses[self._query_idx]

    def sendLine(self, s):
        #print('->', s)
        LineReceiver.sendLine(self, s)

    def send_recv(self, line):
        self._deferred = defer.Deferred()
        self.sendLine(line)
        return self._deferred

    @defer.inlineCallbacks
    def send_query(self, addr, command, arg='', ret_int=False):
        ret_addr = yield self.send_recv('A%s' % (addr, ))
        if ret_addr != addr:
            print('Expected address: %s' % addr)
            print('     Got address: %s' % ret_addr)
            defer.returnValue(None)
        arg = arg.replace(' ', '')
        if command in ('W', ):
            assert((len(arg) % 2) == 0)
            self.sendLine('%s%.2x%s' % (command, len(arg) / 2, arg))
        else:
            self.sendLine('%s%s' % (command, arg))
        ret = yield self.send_recv(command)
        if ret_int:
            ret = hex_str_to_int(ret)
        defer.returnValue(ret)

    def lineReceived(self, line):
        line = line.strip('\0')
        if not self._searched:
            line = line.strip()
            if line:
                self._addresses.add(line)
                self.sendLine('s')
            else:
                self._addresses = tuple(self._addresses)
                print('All addresses (%d):' % (len(self._addresses)))
                for addr in self._addresses:
                    print('\t%s' % addr)

                with open('addresses-%d.txt' % self.port, 'wt') as f:
                    for addr in self._addresses:
                        print(addr, file=f)
                
                reactor.stop()                    
                return

                self._searched = True
                self._query_idx = -1
                self.start_loop()

        elif self._deferred is not None:
            #print('<-', line)
            d, self._deferred = self._deferred, None
            d.callback(line)
        else:
            print('<-?', line)

    def connectionLost(self, reason):
        try:
            d, self._deferred = self._deferred, None
            d.cancel()
        except:
            pass


class HA7EFactory(protocol.ClientFactory):
    protocol = HA7EClient
    def clientConnectionFailed(self, connector, reason):
        print("Connection failed")
        try:
            reactor.stop()
        except:
            pass
    def clientConnectionLost(self, connector, reason):
        try:
            reactor.stop()
        except:
            pass
        else:
            print("Connection lost")


# def save_temperatures():
#     from simple_table import SimpleTable
#     headers, columns = list(temperatures.keys()), \
#                        list(temperatures.values())
#     def fix_col(list_):
#         return ['%g C' % temp for temp in list_]
#     columns = [fix_col(c) for c in columns]
#     table = SimpleTable.from_columns(columns, headers=headers)
#     with open('results.txt', 'wt') as f:
#         table.print_(f=f)


def main():
    global port
    global running
    f = HA7EFactory()
    
    try:
        port = int(sys.argv[1])    
    except:
        pass

    HA7EClient.port = port

    reactor.connectTCP(ip_address, port, f)
    #reactor.addSystemEventTrigger('before', 'shutdown', save_temperatures)
    reactor.run()


if __name__ == '__main__':
    main()
