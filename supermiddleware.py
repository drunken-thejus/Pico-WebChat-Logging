from fastapi.responses import Response,RedirectResponse
from fastapi.requests import Request
from fastapi.responses import FileResponse

async def supermiddleware(request: Request, call_next):
    username=request.cookies.get("token")
    url_path=request.url.path

    if username:
        request.state.username=username
        if url_path=="/":
            return RedirectResponse(f"/chat/{username}")
        else:
            return await call_next(request)
    else:
        if url_path!="/":
            return await call_next(request)
        return await call_next(request)