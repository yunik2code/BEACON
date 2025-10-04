from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def observe():
    return {"message": "Observe Page"}
