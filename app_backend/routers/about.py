from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def about():
    return {"message": "About Us"}
