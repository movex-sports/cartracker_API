"""Async TCP receiver for G900L/J16 trackers using the GT06 protocol."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field

from gt06 import FrameBuffer, build_ack, decode_heartbeat, decode_imei, decode_location, parse_packet


ACK_PROTOCOLS = {0x01, 0x13, 0x16, 0x23}
LOCATION_PROTOCOLS = {0x12, 0x22}


@dataclass
class Session:
    peer: object
    imei: str | None = None
    state: dict[str, object] = field(default_factory=dict)


async def handle_tracker(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    session = Session(writer.get_extra_info("peername"))
    frames = FrameBuffer()
    logging.info("tracker connected peer=%s", session.peer)
    try:
        while data := await reader.read(4096):
            logging.info("received peer=%s bytes=%s", session.peer, data.hex(" "))
            for raw_frame in frames.feed(data):
                try:
                    packet = parse_packet(raw_frame)
                    event: dict[str, object] = {
                        "peer": str(session.peer),
                        "imei": session.imei,
                        "protocol": f"0x{packet.protocol:02x}",
                        "serial": packet.serial.hex(),
                        "crc_valid": packet.valid_crc,
                        "raw": raw_frame.hex(),
                    }
                    if not packet.valid_crc:
                        logging.warning("invalid packet %s", json.dumps(event))
                        continue
                    if packet.protocol == 0x01:
                        session.imei = decode_imei(packet.information)
                        event["imei"] = session.imei
                        event["type"] = "login"
                    elif packet.protocol in LOCATION_PROTOCOLS:
                        event["type"] = "location"
                        event["data"] = decode_location(packet)
                    elif packet.protocol == 0x13:
                        event["type"] = "heartbeat"
                        session.state.update(decode_heartbeat(packet))
                        event["data"] = session.state.copy()
                    else:
                        event["type"] = "unknown"
                        event["information"] = packet.information.hex()
                    logging.info("event=%s", json.dumps(event, ensure_ascii=False))
                    if packet.protocol in ACK_PROTOCOLS:
                        response = build_ack(packet)
                        writer.write(response)
                        await writer.drain()
                        logging.info("sent imei=%s bytes=%s", session.imei, response.hex(" "))
                except (ValueError, IndexError) as error:
                    logging.exception("could not decode frame=%s error=%s", raw_frame.hex(), error)
    except (ConnectionError, asyncio.CancelledError):
        pass
    finally:
        writer.close()
        await writer.wait_closed()
        logging.info("tracker disconnected peer=%s imei=%s", session.peer, session.imei)


async def main() -> None:
    host = os.getenv("GT06_HOST", "0.0.0.0")
    port = int(os.getenv("GT06_PORT", "5023"))
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    server = await asyncio.start_server(handle_tracker, host, port)
    addresses = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
    logging.info("GT06 server listening on %s", addresses)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
