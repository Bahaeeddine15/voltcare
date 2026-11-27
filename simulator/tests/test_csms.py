
import asyncio

import pytest
import websockets
from ocpp.v16 import ChargePoint, call


@pytest.mark.asyncio
async def test_boot_notification():
    async with websockets.connect(
        "ws://localhost:9000/MRK-001",
        subprotocols=["ocpp1.6"]
    ) as websocket:

        borne = ChargePoint("MRK-001", websocket)
        tache = asyncio.create_task(borne.start())

        try:
            reponse = await asyncio.wait_for(
                borne.call(
                    call.BootNotification(
                        charge_point_vendor="VoltCare",
                        charge_point_model="SimBorne"
                    )
                ),
                timeout=20
            )

            assert reponse.status == "Accepted"
            print("BootNotification : Accepted")

        finally:
            tache.cancel()

            try:
                await tache
            except asyncio.CancelledError:
                pass

from ocpp.v16.enums import ChargePointErrorCode, ChargePointStatus


@pytest.mark.asyncio
async def test_status_notification():
    async with websockets.connect(
        "ws://localhost:9000/MRK-001",
        subprotocols=["ocpp1.6"]
    ) as websocket:

        borne = ChargePoint("MRK-001", websocket)
        tache = asyncio.create_task(borne.start())

        try:
            reponse = await asyncio.wait_for(
                borne.call(
                    call.StatusNotification(
                        connector_id=1,
                        error_code=ChargePointErrorCode.no_error,
                        status=ChargePointStatus.available
                    )
                ),
                timeout=10
            )

            assert reponse is not None
            print("StatusNotification : reponse recue")

        finally:
            tache.cancel()

            try:
                await tache
            except asyncio.CancelledError:
                pass

@pytest.mark.asyncio
async def test_heartbeat():
    async with websockets.connect(
        "ws://localhost:9000/MRK-001",
        subprotocols=["ocpp1.6"]
    ) as websocket:

        borne = ChargePoint("MRK-001", websocket)
        tache = asyncio.create_task(borne.start())

        try:
            reponse = await asyncio.wait_for(
                borne.call(call.Heartbeat()),
                timeout=10
            )

            assert reponse.current_time is not None
            print("Heartbeat : reponse recue")

        finally:
            tache.cancel()

            try:
                await tache
            except asyncio.CancelledError:
                pass

from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_start_transaction():
    async with websockets.connect(
        "ws://localhost:9000/MRK-001",
        subprotocols=["ocpp1.6"]
    ) as websocket:

        borne = ChargePoint("MRK-001", websocket)
        tache = asyncio.create_task(borne.start())

        try:
            reponse = await asyncio.wait_for(
                borne.call(
                    call.StartTransaction(
                        connector_id=1,
                        id_tag="CLI-0001",
                        meter_start=0,
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                ),
                timeout=10
            )

            assert reponse.transaction_id > 0
            assert reponse.id_tag_info["status"] == "Accepted"

            print("StartTransaction : Accepted")
            print("Transaction ID :", reponse.transaction_id)

        finally:
            tache.cancel()

            try:
                await tache
            except asyncio.CancelledError:
                pass

@pytest.mark.asyncio
async def test_meter_values():
    async with websockets.connect(
        "ws://localhost:9000/MRK-001",
        subprotocols=["ocpp1.6"]
    ) as websocket:

        borne = ChargePoint("MRK-001", websocket)
        tache = asyncio.create_task(borne.start())

        try:
            mesures = [
                ("Energy.Active.Import.Register", "1539800", "Wh"),
                ("Power.Active.Import", "21800", "W"),
                ("Voltage", "230.4", "V"),
                ("Current.Import", "31.6", "A"),
                ("Temperature", "47.2", "Celsius"),
            ]

            reponse = await asyncio.wait_for(
                borne.call(
                    call.MeterValues(
                        connector_id=1,
                        meter_value=[{
                            "timestamp": datetime.now(
                                timezone.utc
                            ).isoformat(),
                            "sampled_value": [
                                {
                                    "value": valeur,
                                    "measurand": nom,
                                    "unit": unite
                                }
                                for nom, valeur, unite in mesures
                            ]
                        }]
                    )
                ),
                timeout=10
            )

            assert reponse is not None
            print("MeterValues : reponse recue")

        finally:
            tache.cancel()
            try:
                await tache
            except asyncio.CancelledError:
                pass

@pytest.mark.asyncio
async def test_stop_transaction():
    async with websockets.connect(
        "ws://localhost:9000/MRK-001",
        subprotocols=["ocpp1.6"]
    ) as websocket:

        borne = ChargePoint("MRK-001", websocket)
        tache = asyncio.create_task(borne.start())

        try:
            # 1. Démarrer une session de recharge
            debut = await asyncio.wait_for(
                borne.call(
                    call.StartTransaction(
                        connector_id=1,
                        id_tag="CLI-0001",
                        meter_start=1000,
                        timestamp=datetime.now(
                            timezone.utc
                        ).isoformat()
                    )
                ),
                timeout=10
            )

            assert debut.transaction_id > 0

            # 2. Terminer cette même session
            fin = await asyncio.wait_for(
                borne.call(
                    call.StopTransaction(
                        transaction_id=debut.transaction_id,
                        meter_stop=4200,
                        timestamp=datetime.now(
                            timezone.utc
                        ).isoformat(),
                        reason="Local"
                    )
                ),
                timeout=10
            )

            assert fin is not None
            print("StopTransaction : reponse recue")
            print("Transaction ID :", debut.transaction_id)

        finally:
            tache.cancel()

            try:
                await tache
            except asyncio.CancelledError:
                pass

@pytest.mark.asyncio
async def test_session_complete():
    async with websockets.connect(
        "ws://localhost:9000/MRK-001",
        subprotocols=["ocpp1.6"]
    ) as websocket:

        borne = ChargePoint("MRK-001", websocket)
        tache = asyncio.create_task(borne.start())

        try:
            timestamp = datetime.now(timezone.utc).isoformat()

            # 1. Démarrer la recharge
            debut = await asyncio.wait_for(
                borne.call(
                    call.StartTransaction(
                        connector_id=1,
                        id_tag="CLI-0001",
                        meter_start=1000,
                        timestamp=timestamp
                    )
                ),
                timeout=10
            )

            transaction_id = debut.transaction_id
            assert transaction_id > 0

            # 2. Envoyer les mesures pendant la recharge
            mesures = [
                ("Energy.Active.Import.Register", "2500", "Wh"),
                ("Power.Active.Import", "7000", "W"),
                ("Voltage", "230", "V"),
                ("Current.Import", "30.4", "A"),
                ("Temperature", "38.5", "Celsius"),
            ]

            reponse_mesures = await asyncio.wait_for(
                borne.call(
                    call.MeterValues(
                        connector_id=1,
                        transaction_id=transaction_id,
                        meter_value=[{
                            "timestamp": datetime.now(
                                timezone.utc
                            ).isoformat(),
                            "sampled_value": [
                                {
                                    "value": valeur,
                                    "measurand": nom,
                                    "unit": unite
                                }
                                for nom, valeur, unite in mesures
                            ]
                        }]
                    )
                ),
                timeout=10
            )

            assert reponse_mesures is not None

            # 3. Terminer la recharge
            reponse_fin = await asyncio.wait_for(
                borne.call(
                    call.StopTransaction(
                        transaction_id=transaction_id,
                        meter_stop=4200,
                        timestamp=datetime.now(
                            timezone.utc
                        ).isoformat(),
                        reason="Local"
                    )
                ),
                timeout=10
            )

            assert reponse_fin is not None

            print(f"Session complete : transaction_id={transaction_id}")

        finally:
            tache.cancel()

            try:
                await tache
            except asyncio.CancelledError:
                pass
