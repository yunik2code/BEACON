from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def rent_spot():
    return {"message": "Rent a Spot Page"}
