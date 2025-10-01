
"""Modular Modbus/TCP demo exposing airflow, temperature, humidity sensors
and a two‑speed fan motor using pyModbusTCP.

Run as root if you bind to privileged ports (<= 1024).

This file wires together the modular pieces:
 - data_model: address map & scaling
 - sensors: simulation of sensor readings
 - fan: fan control & state simulation
"""

import argparse
import logging
import threading
import time

from pyModbusTCP.server import ModbusServer

from .data_model import DataModel
from .sensors import SensorSimulator
from .fan import FanController


def build_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', type=str, default='localhost', help='Host (default: localhost)')
    parser.add_argument('-p', '--port', type=int, default=5002, help='TCP port (default: 5002), use 502 for standard Modbus/TCP port with root')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--interval', type=float, default=1.0, help='Simulation update interval seconds (default 1.0)')
    return parser


def main():
    args = build_arg_parser().parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    log = logging.getLogger('app')

    # Create server in non-blocking mode so we can update registers.
    server = ModbusServer(host=args.host, port=args.port, no_block=True)
    # Share the server's internal DataBank so network writes reflect in our model
    data_model = DataModel(server.data_bank)
    fan = FanController(data_model)
    sensors = SensorSimulator(data_model, fan)

    def loop():
        while True:
            if server.is_run:  # only update while server running
                fan.update()
                sensors.update()
            time.sleep(args.interval)

    # Start background thread
    threading.Thread(target=loop, daemon=True).start()

    log.info('Starting Modbus server on %s:%s', args.host, args.port)
    server.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info('Stopping Modbus server...')
        server.stop()


if __name__ == '__main__':
    main()