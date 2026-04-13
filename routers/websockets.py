from fastapi import APIRouter
from tools.socket_pico_connections import active_connections,pico_connections
from fastapi.websockets import WebSocket,WebSocketDisconnect
from tools.superdb import *
import  json
from tools.pico_ai import *
import asyncio

import logging

logger=logging.getLogger(__name__)



router=APIRouter()


@router.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    # Reject duplicate usernames
    if username in active_connections:
        await websocket.accept()
        await websocket.send_text(json.dumps({
            "type": "error",
            "data": {"log": f'Username "{username}" is already taken. Please choose another.'}
        }))
        logger.error("duplicate_username",extra={
            "event":"duplicate_username",
            "endpoint":"/ws/",
            "username":username,
            
        })
        await websocket.close()
        return

    await websocket.accept()
    logger.info("user_join",extra={
        "event":"user_join",
        "endpoint":"/ws/",
        "username":username,
    })
    active_connections[username] = websocket
    pico_msg=await get_pico(username)
    logger.debug("pico_chat_lookup",extra={
            "event":"pico_chat_lookup",            
            "username":username,
            "found":bool(pico_msg),

        })
    if pico_msg:
        pico_connections[username]=PicoAI()
        pico_connections[username].chat_history=pico_msg["chat_history"]
    else:
        pico_connections[username]=PicoAI()
        pico_connections[username].chat("My name is "+str(username))
        pico_connections[username].chat(PICO_SYSTEM_PROMPT)
    asyncio.create_task(add_pico(username=username))

    # Notify everyone of updated user list
    await broadcast_user_list()

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") == "public":
                # Broadcast to all connected users
                payload = json.dumps({
                    "type": "message",
                    "data": {
                        "type": "public",
                        "sender": username,
                        "message": data.get("message", "")
                    }
                })
                asyncio.create_task(add_public_message(username=username,message=data.get("message","")))

                try:
                    for user, ws in list(active_connections.items()):
                        await ws.send_text(payload)
                    logger.info("public_message_sent",
                                     extra={
                                     "event":"public_messsage_sent",
                                     "sender":username,
                                     "message_lenthg":len(data.get("message",""))

                                     }
                                     )
                except Exception:
                        logger.error("broadcast_public_message_error",
                                     extra={
                                     "event":"broadcast_public_message_error",
                                     "username":username
                                     },
                                     exc_info=True
                                     )

            elif data.get("type") == "private":
                receiver = data.get("receiver")
                if receiver=="PICO":
                    pico_agent=pico_connections[username]
                    response=pico_agent.chat(data["message"])
                    payload = json.dumps({
                            "type": "message",
                            "data": {
                                "type": "private",
                                "sender": "PICO",
                                "message": response
                            }
                        })
                    asyncio.create_task(update_pico_chat(username=username,chat=pico_agent.chat_history))
                    try:
                        await active_connections[username].send_text(payload)
                        logger.info("pico_reply_sent",extra={
                            "event":"pico_reply_sent",
                            "username":username
                        })
                    except Exception:
                        logger.error("pico_reply_failed",extra={
                            "event":"pico_reply_failed",
                            "username":username
                        },exc_info=True)
                    
                else:
                    if receiver and receiver in active_connections:
                        payload = json.dumps({
                            "type": "message",
                            "data": {
                                "type": "private",
                                "sender": username,
                                "message": data.get("message", "")
                            }
                        })
                        asyncio.create_task(add_private_message(sender=username,receiver=receiver,message=data.get("message","")))
                        try:
                            await active_connections[receiver].send_text(payload)
                            logger.info("private_chat_sent",
                                        extra={
                                            "event":"private_chat_sent",
                                            "sender":username,
                                            "receiver":receiver
                                        })
                        except Exception:
                            logger.error("private_chat_failed",
                                         extra={
                                             "event":"private_chat_failed",
                                             "sender":username,
                                             "receiver":receiver
                                         },
                                         exc_info=True
                                         )

    except WebSocketDisconnect:
        pass
    finally:
        logger.info("user_disconnect",extra={
            "event":"user_disconnect",
            "username":username
        })
        active_connections.pop(username, None)
        await broadcast_user_list()


async def broadcast_user_list():
    users=list(active_connections.keys())
    users.append("PICO")
    payload = json.dumps({
        "type": "active-users-list",
        "data": {"users": users}
    })
    logger.info("broadcast_users_list",
                extra={
                    "event":"broadcast_users_list",
                    "active_user_count":len(users)
                })
    for ws in list(active_connections.values()):
        try:
            await ws.send_text(payload)
        except Exception:
            pass
