from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
import numpy as np
from app.services.algorithm_utils import normalize_algorithm_name, compute_continuity
from nxcurve import quality_curve
from app.api.cache import datasets_cache

connected_clients = []

# ✅ Robust thread-safe notification
def safe_notify_clients_projection_ready(dataset_name: str):
    from asyncio import run_coroutine_threadsafe

    async def notify_clients():
        message = json.dumps({
            "type": "projections_ready",
            "dataset": dataset_name
        })
        print(f"📡 Sending: {message}")
        for client in connected_clients:
            try:
                await client.send_text(message)
            except Exception as e:
                print(f"❌ Error notifying client: {e}")

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        run_coroutine_threadsafe(notify_clients(), loop)
    else:
        # fallback for threads
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(notify_clients())
        new_loop.close()

# ⛓️ Your main WebSocket consumer
async def quality_ws(websocket: WebSocket):
    try:
        connected_clients.append(websocket)
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                payload = json.loads(data)

                if payload.get("type") == "pong":
                    print("🔄 Pong received.")
                    continue

                dataset_name = payload.get("dataset_name") + ".csv"
                print(f"📦 Dataset: {dataset_name}")

                if dataset_name not in datasets_cache:
                    await websocket.send_text(json.dumps({"error": f"Dataset '{dataset_name}' not found"}))
                    return

                dataset = datasets_cache[dataset_name]
                if not dataset.ready:
                    await websocket.send_text(json.dumps({"error": "Dataset projections not ready yet"}))
                    return

                X = dataset.X
                y = dataset.y

                n_components = 2 if payload["target_dimension"] == "2D" else 3
                dim_key = "2d" if n_components == 2 else "3d"
                mix_type = payload.get("mix_by").lower()

                if mix_type not in dataset.projections:
                    await websocket.send_text(json.dumps({"error": f"Mix type '{mix_type}' not found in projections"}))
                    return

                total_percentage = sum(algo["percentage"] for algo in payload["algorithms"])
                if total_percentage != 100:
                    await websocket.send_text(json.dumps({"error": "Percentages must sum to 100"}))
                    return

                blended = np.zeros((X.shape[0], n_components))
                for algo in payload["algorithms"]:
                    name = normalize_algorithm_name(algo["name"])
                    weight = algo["percentage"] / 100.0
                    try:
                        projection = dataset.projections[mix_type][dim_key][algo["name"]]
                    except KeyError:
                        await websocket.send_text(json.dumps({"error": f"Projection '{algo['name']}' not available"}))
                        return
                    blended += np.array(projection) * weight

                print("✅ Blended projection computed.")

                await websocket.send_text(json.dumps({
                    "type": "result",
                    "output": blended.tolist(),
                    "y": y
                }))

            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "keepalive"}))

    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        print("❌ Client disconnected")
    except Exception as e:
        print("⚠️ WebSocket error:", e)
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except:
            pass
    finally:
        print("🔒 WebSocket connection closed.")
