import os
from supabase import create_client, Client
from dotenv import load_dotenv
import asyncio
import logging

logger=logging.getLogger(__name__)


load_dotenv()


supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)


########### AI CHAT ####################

async def check_pico(username:str)->bool:
    response=supabase.table("pico").select("username").eq("username",username).execute().data
    if response:
        logger.info("pico_user_found_db",extra={
            "event":"pico_user_found_db",
            "username":username,
        })
        return True
    logger.info("pico_user_not_found_db",extra={
            "event":"pico_user_not_found_db",
            "username":username,
        })
    return False


async def add_pico(username:str)-> bool:
    check=await check_pico(username)
    if not check:
        try:
            supabase.table("pico").insert({"username":username,"chat_history":[]}).execute()
            logger.info("new_pico_user_added_db",extra={
                "event":"new_pico_user_added_db",
                "username":username
            })
            return True
        except Exception:
            logger.error('failed_to_add_new_pico_user',extra={
                "event":"failed_to_add_new_pico_user",
                "username":username
            },
            exc_info=True)
            return False
    else:
        return False
async def update_pico_chat(username:str,chat:list)-> bool:
    try:
        supabase.table("pico").update({"chat_history":chat}).eq("username",username).execute()
        logger.info("pico_chat_update_success",extra={
            "event":"pico_chat_update_success",
            "username":username,
            "chats_count":len(chat)
        })
        return True
    except Exception:
        logger.error("pico_chat_update_failed",extra={
            "event":"pico_chat_update_failed",
            "username":username
        },
        exc_info=True)
        return False
    

async def get_pico(username:str) -> dict|None:
    response=supabase.table("pico").select("chat_history").eq("username",username).execute().data
    if not response:
        logger.info("pico_chat_empty_db",extra={
            "event":"pico_chat_empty_db",
            "username":username
        })
        return None
    logger.info("pico_chat_found_db",extra={
            "event":"pico_chat_found_db",
            "username":username,
            "chat_count": len(response[0].get("chat_history", []))
        })
    return response[0]

############## PUBLIC CHAT ###############################

async def add_public_message(username:str,message:str)->bool:
    try:
        supabase.table("publicchat").insert({"username": username, "message": message}).execute()
        logger.info("public_message_added_db",extra={
            "event":"public_message_added_db",
            "username":username,
            "message_length":len(message)})
        return True
    except Exception:
        logger.error("public_message_insert_failed", extra={
            "event": "public_message_insert_failed",
            "username": username
        }, exc_info=True)
        return False

async def get_public_chats()->list|None:
    response=supabase.table("publicchat").select("username","message","created_at").execute().data
    if not response:
        logger.info("public_chat_empty_db",extra={
            "event":"public_chat_empty_db",
                    })
        return  None
    logger.info("public_chat_found_db",extra={
        "event":"public_chat_found_db",
        "count":len(response)
    })
    return response

############## PRIVATE CHAT ###############################

async def add_private_message(sender:str,receiver:str,message:str)->bool:
    try:
        supabase.table("privatechat").insert({"sender":sender,"receiver":receiver,"message":message}).execute()
        logger.info("private_chat_message_added_db",extra={
            "event":"private_chat_message_added_db",
            "sender":sender,
            "receiver":receiver,
            "message_length":len(message)
        })
        return True
    except Exception:
        logger.error("failed_to_add_private_chat_message_db",extra={
            "event":"failed_to_add_private_chat_message_db",
            "sender":sender,
            "receiver":receiver,
            "message_length":len(message)
        },exc_info=True
        )
        return False

async def get_private_chats(user1:str,user2:str)->list|None:
    response=supabase.table("privatechat").select("sender","receiver","message","created_at").or_(f"and(sender.eq.{user1},receiver.eq.{user2}),and(sender.eq.{user2},receiver.eq.{user1})").execute().data
    if not response:
        logger.info("private_chat_empty_db",extra={
            "event":"private_chat_empty_db",
            "user1":user1,
            "user2":user2
        })
        return  None
    logger.info("private_chat_fetched_db",extra={
            "event":"private_chat_fetched_db",
            "user1":user1,
            "user2":user2,
            "count":len(response)
        })
    return response


async def test_all():
    data1=await get_public_chats()
    data2=await get_private_chats("thejus","superman")
    data3=await get_pico("thejus")
    data4=await check_pico('thejus')
    print(f"Punlic chat:{data1}")
    print(f"Private chat:{data2}")
    print(f"Pico chat:{data3}")
    print(f"Pico user:{data4}")

if __name__=="__main__":
    asyncio.run(test_all())
