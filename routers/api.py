from fastapi import APIRouter
from fastapi.responses import FileResponse
from tools.socket_pico_connections import active_connections
from tools.superdb import *
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.responses  import Response
import logging


logger=logging.getLogger(__name__)

router=APIRouter()



# routers/api.py


@router.get("/api/history/public")
async def public_history():
    data=[]
    try:
        data = await get_public_chats()
        logger.info("public_chat_retrieved",
                    extra={
                        "event":"public_chat_retrieved",
                        "endpoint":"/api/history/public",
                        "count":len(data)
                    })
    except Exception:
        logger.error("public_chat_fetch_failed",
                     extra={
                         "event":"public_chat_fetch_failed",
                         "endpoint":"/api/history/public"
                     },
                     exc_info=True)
    return JSONResponse(data or [])

@router.get("/api/history/private/{other_user}")
async def private_history(request: Request, other_user: str):
    username = getattr(request.state, "username", None)
    data=[]
    try:
        data = await get_private_chats(username, other_user)
        logger.info("private_chat_retrieved",
                    extra={
                        "event":"private_chat_retrieved",
                        "endpoint":"/api/history/private/",
                        "sender":username,
                        "receiver":other_user,
                        "count":len(data)
                    })
    except Exception:
        logger.error("private_chat_fetch_failed",
                     extra={
                         "event":"private_chat_fetch_failed",
                         "endpoint":"/api/history/private/",
                         "sender":username,
                         "receiver":other_user
                     },
                     exc_info=True)
    return JSONResponse(data or [])

@router.get("/api/history/pico")
async def pico_history(request: Request):
    username = getattr(request.state, "username", None)
    try:
        data=[]
        data = await get_pico(username)
        logger.info("pico_history_retrieved",
                    extra={
                        "event":"pico_history_retrieved",
                        "endpoint":"/api/history/pico",
                        "username":username,
                        "count":len(data.get("chat_history", []))
                    })
    except Exception:
        logger.error("pico_history_fetch_failed",
                     extra={
                         "event":"pico_history_fetch_failed",
                         "endpoint":"/api/history/pico",
                         "username":username
                     }
                     ,exc_info=True)
    return JSONResponse(data or {"chat_history": []})


@router.get("/")
async def get_login():
    return FileResponse("templates/login.html")
    
@router.get("/chat/{username}")
async def get_chat(request:Request,response: Response,username:str):
    try:
        file_response=FileResponse("templates/chat.html")
        file_response.set_cookie(key="token",
        value=username,
        httponly=True,
        secure=True,       # required for HTTPS
        samesite="none"
    )
        logger.info("user_chat_page_loaded",extra={
            "event":"user_chat_page_loaded",
            "endpoint":"/chat/",
            "username":username
        })
        return file_response
    except Exception:
        logger.error("user_chat_page_failed",extra={
            "event":"user_chat_page_failed",
            "endpoint":"/chat/",
            "username":username
        },
        exc_info=True)
        return "Something bad happened"

@router.post('/setcookies')
async def setcookie(response:Response,request:Request,username:str):
    try:
        response.set_cookie(key="token",value=username)
        logger.info("cookies_setup_success",extra={
            "event":"cookies_setup_success",
            "endpoint":"/setcookies",
            "username":username
        })
        return f"Cookies set :{username}"
    except Exception:
        logger.error("cookies_setup_failed",extra={
            "event":"cookies_setup_failed",
            "endpoint":"/setcookies",
            "username":username
        },
        exc_info=True)
        return f"Failed to setup cookie"

@router.get("/deletecookie")
async def get_chat(response:Response):
    response.delete_cookie("token")
    logger.info("cookie_deleted", extra={
    "event": "cookie_deleted",
    "endpoint":"/deletecookie"
})
    return "Cookie deleted successfully"


@router.get("/active-users-count")
async def active_users_count():
    try:
        count=len(active_connections)
        logger.info("active_users_count_retrieved",extra={
            "event":"active_users_count_retrieved",
            "endpoint":"/active-users-count",
            "count":count
        })
        return {"data": {"count": count}}
    except Exception:
        logger.error("active_users_count_fetch_failed",extra={
            "event":"active_users_count_fetch_failed",
            "endpoint":"/active-users-count"
        },
        exc_info=True)
        return JSONResponse({"error": "Failed to load users count"}, status_code=500)