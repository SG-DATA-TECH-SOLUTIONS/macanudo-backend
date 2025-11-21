import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Sale,
    SaleCreate,
    SaleItem,
    SalePublic,
    SalesPublic,
)

router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("/", response_model=SalesPublic)
def read_sales(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Sale)
        count = session.exec(count_statement).one()
        statement = select(Sale).offset(skip).limit(limit)
        sales = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Sale)
            .where(Sale.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Sale)
            .where(Sale.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        sales = session.exec(statement).all()

    return SalesPublic(data=sales, count=count)


@router.post("/", response_model=SalePublic)
def create_sale(
    *, session: SessionDep, current_user: CurrentUser, sale_in: SaleCreate
) -> Any:
    # Create sale
    sale = Sale.model_validate(
        sale_in, update={"owner_id": current_user.id}, exclude={"items"}
    )
    session.add(sale)
    session.commit()
    session.refresh(sale)

    # Create items
    for item in sale_in.items:
        sale_item = SaleItem.model_validate(item, update={"sale_id": sale.id})
        session.add(sale_item)
    
    session.commit()
    session.refresh(sale)
    return sale