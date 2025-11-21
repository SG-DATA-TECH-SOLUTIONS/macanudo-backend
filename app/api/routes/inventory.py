from typing import Any

from fastapi import APIRouter
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    InventoryAdjustment,
    InventoryAdjustmentCreate,
    InventoryAdjustmentPublic,
    InventoryAdjustmentsPublic,
    Product,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/adjustments", response_model=InventoryAdjustmentsPublic)
def read_adjustments(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(InventoryAdjustment)
        count = session.exec(count_statement).one()
        statement = select(InventoryAdjustment).offset(skip).limit(limit)
        adjustments = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(InventoryAdjustment)
            .where(InventoryAdjustment.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(InventoryAdjustment)
            .where(InventoryAdjustment.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        adjustments = session.exec(statement).all()

    return InventoryAdjustmentsPublic(data=adjustments, count=count)


@router.post("/adjustments", response_model=InventoryAdjustmentPublic)
def create_adjustment(
    *, session: SessionDep, current_user: CurrentUser, adjustment_in: InventoryAdjustmentCreate
) -> Any:
    # Log adjustment
    adjustment = InventoryAdjustment.model_validate(
        adjustment_in, update={"owner_id": current_user.id}
    )
    session.add(adjustment)
    
    # Update product stock
    product = session.get(Product, adjustment_in.product_id)
    if product and product.owner_id == current_user.id:
        # Logic depends on type: 'waste' reduces stock, 'additional-use' reduces stock?
        # Assuming negative quantity comes from frontend or we handle it here.
        # For now, simply adding the quantity (assuming frontend sends negative for waste)
        product.current_stock += adjustment_in.quantity
        session.add(product)

    session.commit()
    session.refresh(adjustment)
    return adjustment