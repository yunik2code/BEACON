from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def track_object():
    return {"message": "Track an Object's Path Page"}
